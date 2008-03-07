from zope.interface import Interface
from zope.schema import ASCII
from zope.schema import Datetime
from zope.schema import Iterable
from zope.schema import Text
from zope.schema import TextLine

class ICanFeed(Interface):
    """Marker interface to mean that component can create feeds"""

class IFeedData(Interface):
    """interface to expose necessary data for feed creation"""

    title = TextLine()
    link = ASCII()
    description = Text()
    date = TextLine()
    language = TextLine()
    pubDate = Datetime()
    author = TextLine()
    items = Iterable()

class IFeedItem(Interface):
    """interface that each feed item should implement"""

    title = TextLine()
    link = ASCII()
    description = Text()
    pubDate = Datetime()
