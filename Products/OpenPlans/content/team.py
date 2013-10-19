from AccessControl import ClassSecurityInfo
from BTrees.OOBTree import OOBTree
from DateTime import DateTime
from Products.Archetypes.public import registerType
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType
from opencore.configuration import DEFAULT_ROLES
from Products.TeamSpace.exceptions import MemberRoleNotAllowed
from Products.TeamSpace.permissions import ManageTeam, ViewTeam
from Products.TeamSpace.permissions import ManageTeamMembership
from Products.TeamSpace.team import Team, team_type_information
from opencore.interfaces import IOpenTeam
from opencore.interfaces.event import ChangedTeamRolesEvent
from opencore.nui.indexing import queueObjectReindex
from opencore.utils import get_workflow_policy_config
from zExceptions import Redirect
from zope.event import notify
from zope.interface import implements

marker = object()

openteam_schema = Team.schema.copy()


class OpenTeam(Team):
    """
    OpenPlans team object.
    """
    security = ClassSecurityInfo()

    archetype_name = portal_type = meta_type = "OpenTeam"
    schema = openteam_schema

    implements(IOpenTeam)

    actions = (
        {
        'name'          : 'Membership',
        'id'            : 'view',
        'action'        : 'string:$object_url/openteam_membership',
        'permissions'   : (ViewTeam,),
        'category'      : 'object',
        },
        {
        'name'         : 'Member Roles',
        'id'           : 'member_roles',
        'action'       : 'ts_team_manage_roles',
        'permissions'  : (ManageTeam,),
        'category'     : 'object',
        },
        {
        'name'         : 'Edit',
        'id'           : 'edit',
        'action'       : 'base_edit',
        'permissions'  : (ManageTeam,),
        'category'     : 'object',
        'visible'      : False,
        },
        {
        'name'         : 'Properties',
        'id'           : 'metadata',
        'action'       : 'base_metadata',
        'permissions'  : (ManageTeam,),
        'category'     : 'object',
        },
        )

    aliases = {
        '(Default)'   : 'openteam_membership',
        'view'        : '(Default)',
        'edit'        : 'base_edit',
        'gethtml'     : '',
        'index.html'  : '(Default)',
        'properties'  : '',
        'sharing'     : '',
        'subscribers' : '',
        }

    def getProject(self):
        """
        See IOpenTeam.
        """
        spaces = self.getTeamSpaces()
        if spaces:
            return spaces[0]

    security.declarePrivate('setTeamRolesForMember')
    def setTeamRolesForMember(self, mem_id, roles):
        """
        See IOpenTeam.
        """
        roles_map = getattr(self, '_team_roles_map', marker)
        if roles_map is marker:
            roles_map = self._team_roles_map = OOBTree()

        if mem_id not in self.getMemberIds():
            raise ValueError, "%s not a member of team %s" % (mem_id,
                                                              self.getId())

        allowed_roles = self.getAllowedTeamRoles()
        invalid_roles = set(roles).difference(set(allowed_roles))
        if invalid_roles:
            raise MemberRoleNotAllowed, \
                  "The following roles are not allowed team roles: %s" \
                  % str(list(invalid_roles))

        roles_map[mem_id] = list(roles)

        mship_object = self.getMembershipByMemberId(mem_id)
        notify(ChangedTeamRolesEvent(mship_object))

    security.declarePrivate('getTeamRolesForMember')
    def getTeamRolesForMember(self, mem_id):
        """
        See IOpenTeam.
        """
        roles = []
        roles_map = getattr(self, '_team_roles_map', marker)
        if roles_map is not marker:
            roles = roles_map.get(mem_id, [])
        return roles

    security.declarePrivate('getHighestTeamRoleForMember')
    def getHighestTeamRoleForMember(self, mem_id):
        """
        See IOpenTeam.
        """
        roles = self.getTeamRolesForMember(mem_id)
        if not roles:
            return
        highest_index = 0
        for role in roles:
            index = DEFAULT_ROLES.index(role)
            if index > highest_index:
                highest_index = index
        return DEFAULT_ROLES[highest_index]

    security.declarePrivate('admin_ids')
    # don't use property, because breaks acquisition wrapped when getMembershipBrains
    # tries to get the portal_catalog
    def get_admin_ids(self):
        """
        Returns the user id for each team member with ProjectAdmin
        role.
        """
        brains = self.getMembershipBrains()
        res = []
        active_states = self.getActiveStates()
        for brain in brains:
            if brain.review_state in active_states and \
                   brain.highestTeamRole == 'ProjectAdmin':
                res.append(brain.getId)
        return res

    security.declarePublic('join')
    def join(self):
        """
        Apply for project membership for the currently authenticated member.
        
        Will either create a new membership object or fire
        the rerequest transition (if a membership already exists).

        Can't delegate to addMember b/c we need to bypass the security
        checks when creating the membership object.

        Returns True if the action was successful, False if not.
        """
        ret = True
        putils = getToolByName(self, 'plone_utils')
        mtool = getToolByName(self, 'portal_membership')
        mem = mtool.getAuthenticatedMember()

        mem_id = mem.getId()

        if mem_id not in self.getMemberIds():
            self._createMembership(mem)

        elif mem_id not in self.getActiveMemberIds():
            wftool = getToolByName(self, 'portal_workflow')
            mship = self.getMembershipByMemberId(mem_id)
            try:
                wftool.doActionFor(mship, 'rerequest')
            except WorkflowException:
                # transition isn't available
                ret = False

        else: # mem_id in self.getActiveMemberIds(), nothing to do
            ret = False

        return ret

    security.declarePrivate('joinAndApprove')    
    def joinAndApprove(self, mem=None, made_active_date=None, unlisted=False):
        """
        this makes the currently logged in user (or the provided user)
        a member of this team, forcefully, and optionally backdate the
        membership
        """
        mship = self._createMembership(mem=mem)
        wftool = getToolByName(self, 'portal_workflow')

        # XXX hack around workflow transition
        # pretend we execucted approve_public
        pwft = getToolByName(self, 'portal_placeful_workflow')
        config = get_workflow_policy_config(self)
        if config is not None:
            wfids = config.getPlacefulChainFor('OpenMembership')
            wfid = wfids[0]
        else:
            wfid = 'openplans_team_membership_workflow'
        status = wftool.getStatusOf(wfid, mship)
        status['review_state'] = 'public'
        status['action'] = 'approve_public'
        wftool.setStatusOf(wfid, mship, status)

        if unlisted is True:
            wftool.doActionFor(mship, "make_private")

        # follow up like OpenPlans.Extensions.workflow.mship_activated()
        mship.made_active_date = DateTime(made_active_date)
        mship.reindexObject()
        mship._p_changed = True

    security.declarePrivate('_createMembership')
    def _createMembership(self, mem=None):
        mtool = getToolByName(self, 'portal_membership')
        if mem is None:
            mem = mtool.getAuthenticatedMember()
        mem_id = mem.getId()
        if self.getMembershipByMemberId(mem_id) is not None:
            # already have a membership
            msg = u'You already have a membership on this project.'
            raise ValueError, msg

        mship_type = self.getDefaultMembershipType()
        mship = _createObjectByType(mship_type, self, mem_id)
        refclass = self.membership_reference_class
        mem.addReference(mship,
                         relationship=refclass.relationship,
                         referenceClass=refclass)

        # Assign the default Role to the member
        # We want to assign the default roles to the member
        mship.editTeamRoles(self._default_roles)

        # And notify space objects as these are the most likely
        # subclasses that could hook the event.
        project = self.getProject()
        project._updateMember('add', mem, mship, self)

        return mship

    security.declareProtected(ManageTeamMembership, 'reindexTeamSpaceSecurity')
    def reindexTeamSpaceSecurity(self):
        """
        Override the base class implementation so we can push this job
        into the catalog queue to run asynchronously
        """
        proj = self.getProject()
        queueObjectReindex(self, recursive=True)
        queueObjectReindex(proj, recursive=True)


registerType(OpenTeam)
