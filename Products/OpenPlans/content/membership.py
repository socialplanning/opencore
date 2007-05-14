from zope.interface import implements

from Products.Archetypes.public import registerType
from Products.TeamSpace.membership import TeamMembership

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

registerType(OpenMembership)
