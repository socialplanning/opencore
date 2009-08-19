from AccessControl import ClassSecurityInfo
from Products.Archetypes.public import registerType
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.TeamSpace.membership import TeamMembership
from Products.TeamSpace.permissions import ManageTeamMembership
from opencore.configuration import PROJECTNAME, DEFAULT_ROLES
from opencore.interfaces.membership import IMembershipTransitionEvent
from opencore.interfaces.membership import IOpenMembership
from opencore.interfaces.membership import MembershipTransitionEvent
from opencore.utils import get_workflow_policy_config
from zope import event 
from zope.component import adapter
from zope.interface import implements


class OpenMembership(TeamMembership):
    """
    OpenPlans team membership object.
    """
    archetype_name = portal_type = meta_type = "OpenMembership"

    implements(IOpenMembership)

    security = ClassSecurityInfo()

    intended_visibility = 'public'

    def do_transition(self, transition):
        wftool = getToolByName(self, 'portal_workflow')
        wftool.doActionFor(self, transition)
        event.notify(MembershipTransitionEvent(self, transition))
        
##         after_transition = self.apply_after_transition.get(transition)
##         if after_transition:
##             after_transition(self)

    def getTeamRoles(self):
        """
        Override the default b/c we want to store team roles on the
        team object.
        """
        team = self.getTeam()
        return team.getTeamRolesForMember(self.getId())

    def editTeamRoles(self, team_roles):
        """
        Override the default b/c we want to delegate to the team
        object.
        """
        team = self.getTeam()
        team.setTeamRolesForMember(self.getId(), team_roles)

    security.declarePublic('isProjectCreator')
    def isProjectCreator(self):
        """
        Returns True or False to indicate whether the member
        associated with this membership object is the creator of the
        project / team objects with which the membership is
        associated.

        This method is used as a w/f transition guard.  Have to do it
        here instead of in the guard's TALES expression b/c access to
        the team object isn't possible when it's a closed project.
        """
        team = self.aq_inner.aq_parent
        return team.Creator() == self.getId()

    security.declarePublic('canApprove')
    def canApprove(self, dest_state=None):
        """
        Determines whether the currently authenticated user has the
        right to approve this membership for a given team.

        o dest_state - the intended destination state of the
        transition being evaluated; used to ensure that only the
        transition that results in the desired membership visibility
        is exposed
        """
        if getattr(self, '_v_self_approved', False):
            return True
        
        if dest_state is not None and \
           dest_state != self.intended_visibility:
            return False

        mtool = getToolByName(self, 'portal_membership')
        wftool = getToolByName(self, 'portal_workflow')

        pwft = getToolByName(self, 'portal_placeful_workflow')
        config = get_workflow_policy_config(self.getTeam())
        if config is not None:
            wfids = config.getPlacefulChainFor('OpenMembership')
            # only one in chain
            wfid = wfids[0]
        else:
            wfid = 'openplans_team_membership_workflow'
        wf_hist = wftool.getHistoryOf(wfid, self)
        last_transition = wf_hist[-1]

        review_state = last_transition.get('review_state')
        if review_state == 'pending':
            auth_mem = mtool.getAuthenticatedMember()
            owner_id = self.owner_info()['id']
            actor_id = last_transition.get('actor')

            if actor_id == owner_id:
                # requires project admin approval
                can = mtool.checkPermission(ManageTeamMembership,
                                            self.getTeam())
            else:
                # requires member approval
                can = (owner_id == auth_mem.getId()) or \
                      mtool.checkPermission(ManagePortal, self.getTeam())
                
        elif review_state == 'rejected_by_admin':
            can = mtool.checkPermission(ManageTeamMembership, self.getTeam())
        elif review_state == 'rejected_by_owner':
            auth_mem = mtool.getAuthenticatedMember()
            owner_id = self.owner_info()['id']
            can = owner_id == auth_mem.getId()

        return bool(can)

    def canReject(self, by):
        """
        Determines whether the currently authenticated user has the
        right to reject this membership for a given team.

        o by - should be either 'owner' or 'admin', used to ensure
        that only the transition that results in the correct rejection
        queue will be exposed
        """
        # the canApprove logic mostly applies
        can = self.canApprove()
        if can:
            mtool = getToolByName(self, 'portal_membership')
            auth_mem = mtool.getAuthenticatedMember()
            owner_id = self.owner_info()['id']
            if by == 'owner':
                if auth_mem.getId() != owner_id:
                    can = False
            elif by == 'admin':
                if auth_mem.getId() == owner_id:
                    # owner rejection trumps admin rejection if they
                    # both apply
                    can = False
                elif not mtool.checkPermission(ManageTeamMembership,
                                               self.getTeam()):
                    can = False
        return can

registerType(OpenMembership, package=PROJECTNAME)

def fixupOwnership(obj, event):
    mem = obj.getMember()
    mtool = getToolByName(obj, 'portal_membership')
    auth_mem = mtool.getAuthenticatedMember()
    if mem == auth_mem:
        # don't need to do anything
        return

    obj.manage_delLocalRoles([auth_mem.getId()])
    uf = getToolByName(obj, 'acl_users')
    mem_id = mem.getId()
    user = uf.getUserById(mem_id)
    if user is not None:
        obj.changeOwnership(user)
        obj.manage_setLocalRoles(mem_id, ('Owner',))


@adapter(IMembershipTransitionEvent)
def post_wf_transition(event=None):
    if event.transition == 'deactivate':
        event.obj.editTeamRoles(DEFAULT_ROLES[:-1])
    # reindex the member
    event.obj.getMember().reindexObject()

