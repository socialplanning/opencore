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
    Marks an object as having the listen featurelet installed, with
    the following effects:

     * a "Mailing Lists" topnav menu item will be displayed when viewing
       the object (in ./browser/configure.zcml)

     * ITellYouAboutContent(object, name='lists') will be usable without
       raising a string exception (in ./query.py)

     * a @@listen_config view will be registered on the object (in
       opencore/featurelets/browser/configure.zcml)

     * a `discussions` viewlet is registered for the object to the
       ISummaryFeeds viewlet manager (in ./feed/configure.zcml)

     * a @@contact-team view will be registered on the object (in
       ./browser/configure.zcml)

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
