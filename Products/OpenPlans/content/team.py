from Products.Archetypes.public import registerType
from Products.TeamSpace.team import Team, team_type_information
from Products.TeamSpace.permissions import ManageTeam, ViewTeam

from zope.interface import implements

from Products.OpenPlans.interfaces import IOpenTeam

openteam_schema = Team.schema.copy()

class OpenTeam(Team):
    """
    OpenPlans team object.
    """

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

registerType(OpenTeam)
