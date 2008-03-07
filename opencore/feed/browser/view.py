from opencore.feed.interfaces import IFeedData
from Products.Five import BrowserView

class RssView(BrowserView):
    """view that simply adapts context to IFeedData
       as promised by marker interface ICanFeed"""

    def __init__(self, context, request):
        adapted = IFeedData(context)
        super(RssView, self).__init__(adapted, request)
