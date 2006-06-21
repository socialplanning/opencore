from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IMailingList

from zope.schema import ASCII
from zope.i18nmessageid import MessageIDFactory

_ = MessageIDFactory('opencore')

class IOpenMailingList(IMailingList):
    """
    Slight customizations to the default listen mailing list schema.
    """
    mailto = ASCII(
        title = _(u"List Address Prefix"),
        description = _(u"The prefix portion of the main address "
                        u"for the mailing list."),
        required = True,
        )

    mailto.order = IMailingList['mailto'].order
