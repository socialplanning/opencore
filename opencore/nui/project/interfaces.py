from zope.interface import Interface
from zope.schema import TextLine

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


class IFeedItem(Interface):
    # XXX any reason these are methods and not using zope.schema?
    # XXX also, where is this used?

    def title():
        """title of the item"""

    def url():
        """location of the item in webspace"""

    def author():
        """author of the item"""

    def date():
        """when the item was modified/created"""

        
class IHomePage(Interface):
    """store a home page attribute on an object"""
    home_page = TextLine(
                    title=u'home page url',
                    description=u"url of object's home page",
                    )
