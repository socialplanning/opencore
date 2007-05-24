from zope.interface import implements

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.public import registerType
from Products.TeamSpace.membership import TeamMembership

from Products.OpenPlans.config import PROJECTNAME
from Products.OpenPlans.interfaces import IOpenMembership

class OpenMembership(TeamMembership):
    """
    OpenPlans team membership object.
    """
    archetype_name = portal_type = meta_type = "OpenMembership"

    implements(IOpenMembership)

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
