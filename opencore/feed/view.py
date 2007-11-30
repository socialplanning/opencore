import feedparser
from dateutil.parser import parse
from opencore.browser.base import BaseView

def date_cmp(entry1, entry2):
    """compare feed entries by date"""
    return cmp(parse(entry1.date), parse(entry2.date))

class FeedView(BaseView):
    def handle_request(self):
        uri = self.request.get('uri')
        n = self.request.get('n', 3)
        if uri:
            self.feed = feedparser.parse(uri)
            self.title = self.request.get('title', self.feed.feed.title)
#            self.feed.entries.sort(cmp=date_cmp) # they appeared sorted already?
            self.feed.entries = self.feed.entries[:n]

