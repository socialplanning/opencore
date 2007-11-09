from warnings import warn
from opencore.interfaces.membership import IEmailInvites
from zope.interface import Interface
from zope.schema import TextLine

warn("!!! %s is deprecated. get put your interfaces from opencore.interfaces" %__name__)


class IFeedItem(Interface):
    # XXX any reason these are methods and not using zope.schema? or attributes?
    # XXX also, where is this used?

    def title():
        """title of the item"""

    def url():
        """location of the item in webspace"""

    def author():
        """author of the item"""

    def date():
        """when the item was modified/created"""

        

