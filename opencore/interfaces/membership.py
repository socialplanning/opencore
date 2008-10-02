# @@ maybe these should go in a team.py
from zope.interface import Interface, Attribute
from zope.interface import implements
from Products.TeamSpace.interfaces.membership import ITeamMembership

class IOpenMembership(ITeamMembership):
    """
    Interface provided by OpenMembership objects.
    """


class IMembershipTransitionEvent(Interface):
    """
    A membership object has made a workflow transition to a new state 
    """
    transition = Attribute('name of the transition')
    obj = Attribute('object that made said transition')


class MembershipTransitionEvent(object):
    implements(IMembershipTransitionEvent)
    def __init__(self, obj, transition):
        self.obj = obj
        self.transition = transition


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
