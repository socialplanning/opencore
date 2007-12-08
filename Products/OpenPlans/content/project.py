from AccessControl import ClassSecurityInfo
from Acquisition import aq_base, aq_parent, aq_inner
from Products.ATReferenceBrowserWidget.ATReferenceBrowserWidget import ReferenceBrowserWidget
from Products.Archetypes.ExtensibleMetadata import ExtensibleMetadata
from Products.Archetypes.config import REFERENCE_CATALOG
from Products.Archetypes.public import *
from Products.Archetypes.utils import shasattr
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.permissions import ManagePortal, View
from Products.CMFCore.permissions import ModifyPortalContent, DeleteObjects
from Products.CMFCore.utils import getToolByName
from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin
from Products.CMFPlone.utils import _createObjectByType
from Products.OpenPlans.permissions import CopyOrMove
from Products.OpenPlans.permissions import ManageWorkflowPolicy
from Products.TeamSpace.space import TeamSpaceMixin
from Products.TeamSpace.space import TeamSpace
from Products.ZCTextIndex import ParseTree
from ZODB.POSException import ConflictError
from opencore.configuration import OC_REQ as OPENCORE
from opencore.interfaces import IProject
from topp.featurelets.config import MENU_ID
from topp.featurelets.interfaces import IMenuSupporter
from zope.app.annotation.interfaces import IAnnotatable
from zope.app.annotation.interfaces import IAttributeAnnotatable
from zope.interface import Interface, implements
import os.path
import pkg_resources

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

        ImageField('logo',
          mode='rw',
          accessor='getLogo',
          mutator='setLogo',
          max_size=(150,150),
          widget=ImageWidget(
            label='Logo',
            label_msgid='label_logo',
            description="",
            description_msgid='help_logo',
            i18n_domain='plone',
            ),
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

# items for the 'breadcrumbs' menu bar
# XXX these should probably live elsewhere, maybe in 
# _initProjectHomeMenuItem

project_menu_item = {'title': u'Project Home',
                     'description': u'Project Home',
                     'action': '',
                     'extra': None,
                     'order': 0,
                     'permission': None,
                     'filter': None,
                     'icon': None,
                     '_for': Interface,
                     }

project_menu_preferences = {'title': u'Project Preferences',
                            'description': u'Project Preferences',
                            'action': 'base_edit',
                            'extra': None,
                            'order': 0,
                            'permission': 'ManageWorkflowPolicy',
                            'filter': None,
                            'icon': None,
                            '_for': Interface,
                            }

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
    home_page_title = 'Project Home'
    home_page_file = 'project_index.html'

    _at_rename_after_creation = True

    # put reasonable guards on the renaming methods
    security.declareProtected(DeleteObjects, 'manage_renameObjects')
    security.declareProtected(DeleteObjects, 'manage_renameObject')

    # put reasonable guards on the CopySupport methods
    security.declareProtected(CopyOrMove, 'manage_copyObjects')
    security.declareProtected(CopyOrMove, 'manage_pasteObjects')
    security.declareProtected(CopyOrMove, 'manage_renameObjects')
    security.declareProtected(CopyOrMove, 'manage_renameObject')
    security.declareProtected(CopyOrMove, 'manage_renameForm')

    # Rename the edit action for consistency
    actions = ({
        'id'          : 'edit',
        'name'        : 'Project Preferences',
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
        self.invokeFactory('Document', self.home_page_id,
                           title=self.home_page_title)
        page = self._getOb(self.home_page_id)
        page_file = pkg_resources.resource_stream(OPENCORE, 'copy/%s' %self.home_page_file)
        page.setText(page_file.read())

    def _initProjectHomeMenuItem(self):
        """
        Sets up an initial 'project home' menu item in the featurelets
        menu.
        """        
        menusupporter = IMenuSupporter(self)
        menu_item = project_menu_item.copy()
        menusupporter.addMenuItem(MENU_ID, menu_item)
        menu_item = project_menu_preferences.copy()
        menusupporter.addMenuItem(MENU_ID, menu_item)

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
        if admin_only:
            # XXX we need this
            pass
        else:
            for team in teams:
                members.update(set(team.getActiveMemberIds()))
        return tuple(members)

    security.declareProtected(View, 'projectMembers')
    def projectMembers(self, admin_only=False):
        """Compute all the members of this project in a nice way
        """
        members = []
        if admin_only:
            pass
        else:
            # We don't have a contact with members that says they have
            # to support __hash__ so we do this...
            member_ids = self.projectMemberIds()
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

registerType(OpenProject)
