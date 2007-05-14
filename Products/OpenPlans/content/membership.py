from Products.Archetypes.public import registerType
from Products.TeamSpace.membership import TeamMembership

class OpenMembership(TeamMembership):
    """
    OpenPlans team membership object.
    """
    archetype_name = portal_type = meta_type = "OpenMembership"

registerType(OpenMembership)
