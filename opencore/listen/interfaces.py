from zope.schema import ASCII
from zope.i18nmessageid import MessageFactory
from zope.interface import Interface

from Products.listen.interfaces.mailinglist import IMailingList

from utils import isValidPrefix

_ = MessageFactory('opencore')

class IOpenMailingList(IMailingList):
    """
    Slight customizations to the default listen mailing list schema.
    """
    mailto = ASCII(
        title = _(u"listen_address_prefix", u"List Address Prefix"),
        description = _(u"listen_address_prefix_description", u"The prefix portion of the main address "
                        u"for the mailing list."),
        required = True,
        constraint = isValidPrefix,
        )

    mailto.order = IMailingList['mailto'].order

#marker interfaces for listen featurelet

class IListenFeatureletInstalled(Interface):
    """
    Marks an object as having the listen featurelet installed.
    """

class IListenContainer(Interface):
    """
    Marks an object as a mailing list container for the listen
    featurelet.
    """

class ISyncWithProjectMembership(Interface):
    """
    When a mailing list is marked w/ this interface it will respond to
    member joined / removed events to stay in sync w/ the project
    membership.

    Project membership is determined and manipulated by IWriteMembershipList,
    so any list marked ISyncWithProjectMembership must also be adaptable
    to IWriteMembershipList.
    """
