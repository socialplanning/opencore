from AccessControl import ClassSecurityInfo
from Acquisition import aq_inner
from Products.ATReferenceBrowserWidget.ATReferenceBrowserWidget import ReferenceBrowserWidget
from Products.Archetypes.Field import Image
from Products.Archetypes.public import BaseBTreeFolder
from Products.Archetypes.public import ComputedField
from Products.Archetypes.public import ComputedWidget
from Products.Archetypes.public import ImageWidget
from Products.Archetypes.public import Schema
from Products.Archetypes.public import StringField
from Products.Archetypes.public import StringWidget
from Products.Archetypes.public import registerType
from Products.Archetypes.utils import shasattr
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.permissions import ManagePortal, View
from Products.CMFCore.permissions import ModifyPortalContent, DeleteObjects
from Products.CMFCore.utils import getToolByName
from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin
from Products.CMFPlone.utils import _createObjectByType
from Products.OpenPlans.permissions import CopyOrMove
from Products.TeamSpace.space import TeamSpace
from Products.TeamSpace.space import TeamSpaceMixin
from Products.ZCTextIndex import ParseTree
from opencore.configuration import DEFAULT_ROLES
from opencore.configuration import OC_REQ as OPENCORE
from opencore.content.fields import SquareScaledImageField
from opencore.interfaces import IProject
from opencore.project.utils import project_noun
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.component import queryMultiAdapter
from zope.interface import Interface, implements
import logging
import os.path
import pkg_resources

logger = logging.getLogger('opencore.Project')

ProjectSchema = TeamSpace.schema.copy()
# Prevent bug 1689 from affecting projects too.
ProjectSchema['id'].searchable = 1

ProjectSchema += Schema((
        ComputedField(
          'full_name',
          index='ZCTextIndex,lexicon_id=plone_lexicon,index_type=Cosine Measure|TextIndex:brains',
          searchable=1,
          accessor='getFull_name',
          expression="context.Title() or context.getId()",
          widget=ComputedWidget(
            label="Full Name",
            label_msgid="label_full_name",
            description_msgid="desc_full_name",
            description="Name of this project.",
            size=50,
            ),
          ),

        SquareScaledImageField('logo',
          mode='rw',
          accessor='getLogo',
          mutator='setLogo',
          max_size=(150,150),
          sizes=dict(thumb=(80,80),
                     square_thumb=(80,80),
                     square_fifty_thumb=(50,50),
                     ),
          widget=ImageWidget(
            label='Logo',
            label_msgid='label_logo',
            description="",
            description_msgid='help_logo',
            i18n_domain='plone',
            ),
          ),
        StringField(
          'location',
          mode='rw',
          read_permission=View,
          write_permission=ModifyPortalContent,
          widget=StringWidget(
            label='Location',
            label_msgid='label_location',
            description="Your location - either city and country - or in a company setting, where your office is located.",
            description_msgid='help_location',
            i18n_domain='plone',
            ),
          searchable=True,
          ),
        ))

ProjectSchema['id'].widget.label = 'URL Name'
ProjectSchema['id'].widget.description = \
      "This is the 'id' of your project.  It will " + \
      "become a part of the URL that people will " + \
      "use to access your project.  It should NOT " + \
      "contain spaces and should be all lowercase. " + \
      "Please choose carefully; it is difficult to " + \
      "change this later."

ProjectSchema['title'].widget.label = 'Name'
ProjectSchema['title'].widget.description = \
      "The name for your project will be " + \
      "used to refer to your project throughout the " + \
      "web site.  Because it is used in a " + \
      "navigation context throughout the site, " + \
      "it is suggested that this be no more than 15 " + \
      "characters"
ProjectSchema['title'].widget.size = 50

ProjectSchema['space_teams'].widget = ReferenceBrowserWidget(
                macro="openteam_refbrowser",
                allow_browse=False,
                label="Teams",
                label_msgid="label_teams",
                description="Search for teams to associate with this Project",
                description_msgid="description_teams",
                helper_js=("openteam_refbrowser.js",),
                visible={'view': 'invisible',
                         'edit': 'invisible',},
                )

ProjectSchema['space_teams'].allowed_types = ('OpenTeam',)
ProjectSchema['space_teams'].write_permission = ManagePortal
ProjectSchema.moveField('space_teams', pos='bottom')


class OpenProject(BrowserDefaultMixin, TeamSpaceMixin, BaseBTreeFolder):
    """
    A Project workspace.
    """

    implements(IProject, IAttributeAnnotatable)

    archetype_name = portal_type = meta_type = "OpenProject"
    global_allow = 1

    schema = ProjectSchema
    security = ClassSecurityInfo()
    content_icon = 'openproject_icon.png'

    home_page_id = 'project-home'
    home_page_file = 'project_index.html'

    _at_rename_after_creation = True

    # put reasonable guards on copy and rename methods
    security.declareProtected(CopyOrMove, 'manage_renameObjects')
    security.declareProtected(CopyOrMove, 'manage_renameObject')
    security.declareProtected(CopyOrMove, 'manage_copyObjects')
    security.declareProtected(CopyOrMove, 'manage_pasteObjects')
    security.declareProtected(CopyOrMove, 'manage_renameForm')

    # Rename the edit action for consistency
    actions = ({
        'id'          : 'edit',
        'name'        : '%s Preferences' % project_noun().title(),
        'action'      : 'string:${object_url}/base_edit',
        'permissions' : (ModifyPortalContent,),
        'visible'     : False,
         },
        {
        'id'          : 'view',
        'name'        : 'View',
        'action'      : 'string:${object_url}',
        'permissions' : (View,)
         },
        {
        'id'          : 'metadata',
        'name'        : 'Properties',
        'action'      : 'string:${object_url}/properties',
        'permissions' : (ModifyPortalContent,),
        'visible'     : False,
         },
        )

    default_project_logos = dict(
        default=dict(name='default', title='Default logo', fname='default-projlogo.gif'),
        thumb=dict(name='thumb', title='Default thumbnail', fname='default-projlogo-thumb.gif'),
        square_thumb=dict(name='thumb', title='Default square thumbnail', fname='default-projlogo-80x80.gif'),
        square_fifty_thumb=dict(name='thumb', title='Default square 50x50 thumbnail', fname='default-projlogo-50x50.gif'),
        )

    def __init__(self, id, title=''):
        BaseBTreeFolder.__init__(self, id)
        self.title = title or self.meta_type

    def _createTeam(self):
        """
        Create and associate a team object.
        """
        p_id = self.getId()
        pt = getToolByName(self, 'portal_teams')
        # Let's not create new objects in an extraneously wrapped container
        pt = aq_inner(pt)
        if not shasattr(pt.aq_base, p_id):
            team = _createObjectByType('OpenTeam', pt, p_id)
            team.setTitle(self.Title())
            self.setSpaceTeams((team,))

            real_team = None
            tms = self.getTeams()
            for tm in tms:
                if tm.getId() == p_id:
                    real_team = tm
                    break
            assert real_team is not None and team.UID() == real_team.UID()
            oid = self.getOwnerTuple()[1]
            membership = team.addMember(oid)
            # Give owner team mgmt privs
            membership.editTeamRoles(['ProjectMember',
                                      'ProjectAdmin'])
            wft = getToolByName(self, 'portal_workflow')
            try:
                wft.doActionFor(membership, 'trigger')
            except WorkflowException:
                pass

    def _createIndexPage(self):
        """
        Create the project index page from the specified file.
        """
        home_page_title = 'Home'
        self.invokeFactory('Document', self.home_page_id,
                           title=home_page_title)
        page = self._getOb(self.home_page_id)
        page_file = pkg_resources.resource_stream(OPENCORE, 'copy/%s' % self.home_page_file)
        page.setText(page_file.read().replace('${project_noun}', project_noun()))

    # Validation
    def _hasDuplicate(self, index, value):
        """
        Checks to see if there is a project in the catalog, other than
        self, with an index value matching the provided value.
        Assumes the index is a text index and that it is stored in the
        catalog metadata.  Considered a duplicate if it contains all
        the same words in the same order, regardless of case or
        whitespace.
        """
        def norm(value):
            return ' '.join(value.lower().split())

        cat = getToolByName(self, 'portal_catalog')
        query = {index: value,
                 'Type': self.Type()}
        try:
            matches = cat(**query)
        except ParseTree.ParseError:
            # parens confuse ZCTextIndex
            illegals = (')', '(',)
            vcopy = value
            for illegal in illegals:
                vcopy = vcopy.replace(illegal, '')
            query = {index: vcopy,
                     'Type': self.Type()}
            matches = cat(**query)
            
        for match in matches:
            if match.UID != self.UID():
                # now we refine the comparison
                if norm(value) == norm(getattr(match, index)):
                    return True
        return False
    
    def validate_title(self, value):
        """
        Don't allow duplicates.  We consider duplicates to be all of
        the same words in the same order, regardless of whitespace or
        capitalization.
        """
        if self._hasDuplicate('Title', value):
            return "This project name is already taken.  Please choose " \
                   "another."

    # Member management
    security.declareProtected(View, 'projectMemberIds')
    def projectMemberIds(self, admin_only=False):
        """Compute all the members of this project in a nice way
        """
        members = set()
        teams = self.getTeams()
        for team in teams:
            ids = team.getActiveMemberIds()
            if admin_only:
                ids = [ i for i in ids
                        if team.getHighestTeamRoleForMember(i) == DEFAULT_ROLES[-1] ]
            members.update(set(ids))

        return tuple(members)

    security.declareProtected(View, 'projectMemberBrains')
    def projectMemberBrains(self, admin_only=False):
        cat = getToolByName(self, 'membrane_tool')
        member_ids = self.projectMemberIds(admin_only=admin_only)
        return tuple(cat(getId=member_ids))

    security.declareProtected(View, 'projectMembers')
    def projectMembers(self, admin_only=False):
        """Compute all the members of this project in a nice way
        """
        members = []
        # We don't have a contract with members that says they have
        # to support __hash__ so we do this...
        member_ids = self.projectMemberIds(admin_only=admin_only)
        pm_tool = getToolByName(self, 'portal_membership')
        for mid in member_ids:
            members.append(pm_tool.getMemberById(mid))
        return tuple(members)

    security.declareProtected(View, 'getTeamRolesForAuthMember')
    def getTeamRolesForAuthMember(self):
        """
        Returns the team roles for the current authenticated member
        """
        mtool = getToolByName(self, 'portal_membership')
        mem = mtool.getAuthenticatedMember()
        team_roles = {}
        teams = self.getTeams()
        for team in teams:
            mship = team.getMembershipByMemberId(mem.getId())
            if mship is not None:
                for role in mship.getTeamRoles():
                    team_roles[role] = 1
        return team_roles.keys()

    def isProjectMember(self, mem_id=None):
        if mem_id is None:
            membertool = getToolByName(self, 'portal_membership')
            mem_id = membertool.getAuthenticatedMember().getId()
        if not mem_id:
            return False
        for team in self.getTeams():
            filter_states = tuple(team.getActiveStates()) + ('pending',)
            if mem_id in team.getMemberIdsByStates(filter_states):
                return True
        return False

    def isProjectAdmin(self, mem_id=None):
        if mem_id is None:
            membertool = getToolByName(self, 'portal_membership')
            mem_id = membertool.getAuthenticatedMember().getId()
        if not mem_id:
            return False

        team = self.getTeams()[0]
        return team.getHighestTeamRoleForMember(mem_id) == DEFAULT_ROLES[-1] 

    def getLogo(self):
        """custom logo accessor in case project contains an OpenPage with id 'logo'"""
        if hasattr(self, 'logo'):
            if not isinstance(self.logo, Image):
                return None
            return self.logo

    def _default_img_data(self, name, request):
        logo = self.default_project_logos.get(name, 'default')
        img_resource_dir = queryMultiAdapter((request,), name='img')
        if img_resource_dir is None:
            # for hysterical reasons.  This lookup failed on one known
            # project (openplans.org/projects/nycstreets) which prevented
            # reindexing the references_catalog.
            logger.error("Could not look up 'img' view for project %r" %
                         self.getId())
            data = ''
        else:
            imgpath = img_resource_dir.context.path
            f = open(os.path.join(imgpath, logo['fname']))
            data = f.read()
            f.close()
        im = Image(logo['name'], logo['title'], data)
        return im

    def __bobo_traverse__(self, REQUEST, name):
        """Transparent access to image scales
           **adapted from ATCT**

           If request looks like a request for a logo, but the proper scale
           isn't found, then we return back the default logo for the requested
           scale.
        """
        if name.startswith('logo'):
            field = self.getField('logo')
            image = None
            if name == 'logo':
                image = field.getScale(self)
                if not image:
                    return self._default_img_data('default', REQUEST).__of__(self)
            else:
                scalename = name[len('logo_'):]
                if scalename in field.getAvailableSizes(self):
                    image = field.getScale(self, scale=scalename)
                    if not image:
                        return self._default_img_data(scalename, REQUEST).__of__(self)
            if image:
                # image might be None or '' for empty images
                return image

        return super(OpenProject, self).__bobo_traverse__(REQUEST, name)

registerType(OpenProject, 'Products.OpenPlans')
