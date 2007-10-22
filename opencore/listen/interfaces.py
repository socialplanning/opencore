from Products.listen.interfaces.mailinglist import IMailingList

from zope.schema import ASCII
from zope.i18nmessageid import MessageIDFactory

from utils import isValidPrefix
from config import LIST_SUFFIX as SUFFIX

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
        constraint = isValidPrefix,
        )

    mailto.order = IMailingList['mailto'].order
