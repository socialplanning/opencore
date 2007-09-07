from zope.interface import implements

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ManagePortal
from Products.Archetypes.public import registerType
from Products.TeamSpace.membership import TeamMembership
from Products.TeamSpace.permissions import ManageTeamMembership

from Products.OpenPlans.config import PROJECTNAME
from Products.OpenPlans.interfaces import IOpenMembership

class OpenMembership(TeamMembership):
    """
    OpenPlans team membership object.
    """
    archetype_name = portal_type = meta_type = "OpenMembership"

    implements(IOpenMembership)

    intended_visibility = 'public'

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

    def canApprove(self, dest_state=None):
        """
        Determines whether the currently authenticated user has the
        right to approve this membership for a given team.

        o dest_state - the intended destination state of the
        transition being evaluated; used to ensure that only the
        transition that results in the desired membership visibility
        is exposed
        """
        if dest_state is not None and \
           dest_state != self.intended_visibility:
            return False

        mtool = getToolByName(self, 'portal_membership')
        wftool = getToolByName(self, 'portal_workflow')

        pwft = getToolByName(self, 'portal_placeful_workflow')
        config = pwft.getWorkflowPolicyConfig(self.getTeam())
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
