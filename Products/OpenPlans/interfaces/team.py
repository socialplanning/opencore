from zope.interface import Interface, Attribute


class IOpenTeam(Interface):
    """
    Interface provided by OpenTeam objects.

    XXX: TeamSpace needs to be updated to use Z3 interfaces so we can
    subclass from those.
    """
    def getProject():
        """
        Returns the associated project object.

        Tried to make this a python property, but was getting
        attribute errors from the ProjectInfoView.project method.
        """

    def setTeamRolesForMember(mem_id, roles):
        """
        Sets the team roles for a given team member.

        o mem_id: member id, must be a member of the team (need not be
        active)

        o roles: list of team roles to assign, overwrites any other
        assigned roles.  roles must be a subset of the specified team
        roles
        """

    def getTeamRolesForMember(mem_id):
        """
        Returns the set of team roles assigned to the specified member
        id.  Returns an empty list if the member is not on the team.
        """
