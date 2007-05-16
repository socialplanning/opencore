from BTrees.OOBTree import OOBTree
from AccessControl import ClassSecurityInfo
from Products.Archetypes.public import registerType
from Products.TeamSpace.team import Team, team_type_information
from Products.TeamSpace.permissions import ManageTeam, ViewTeam
from Products.TeamSpace.exceptions import MemberRoleNotAllowed

from zope.interface import implements

from Products.OpenPlans.interfaces import IOpenTeam

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

    security.declarePrivate('setRolesForMember')
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

    security.declarePrivate('getRolesForMember')
    def getTeamRolesForMember(self, mem_id):
        """
        See IOpenTeam.
        """
        roles = []
        roles_map = getattr(self, '_team_roles_map', marker)
        if roles_map is not marker:
            roles = roles_map.get(mem_id, [])
        return roles

registerType(OpenTeam)
