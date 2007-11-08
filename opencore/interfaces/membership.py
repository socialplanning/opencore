from zope.interface import Interface

class IOpenMembership(Interface):
    """
    Interface provided by OpenMembership objects.

    XXX: TeamSpace needs to be updated to use Z3 interfaces so we can
    subclass from those.
    """

class IEmailInvites(Interface):
    """
    Interface for a local utility that tracks the project invitations
    that have been extended to non-site members (by email address).
    """
    def getInvitesByEmailAddress(address):
        """
        Returns a BTree, keys are project ids, values are timestamps
        of when the invitation was extended.
        """

    def getInvitesByProject(proj_id):
        """
        Returns a BTree, keys are email addresses, values are
        timestamps of when the invitation was extended.
        """

    def addInvitation(address, proj_id):
        """
        Registers an invitation to the specified email address for the
        specified project.
        """

    def removeInvitation(address, proj_id):
        """
        Removes the invitation registered for the specified email
        address and project id.

        Does nothing if the invitation doesn't exist.
        """

    def removeAllInvitesForAddress(address):
        """
        Removes registration of all invitations for the specified
        email address.

        Does nothing if no invitations exist for the specified
        address.
        """

    def convertInvitesForMember(member):
        """
        Converts any invitations for the email address related to the
        given member object into actual membership object invitations
        which can be approved per the default interface.
        """
