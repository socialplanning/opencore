from zope.schema import ASCII
from zope.i18nmessageid import MessageIDFactory

from Products.listen.interfaces.mailinglist import IMailingList

from utils import isValidPrefix

_ = MessageIDFactory('opencore')

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
