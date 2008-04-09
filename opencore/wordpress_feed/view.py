import feedparser
from dateutil.parser import parse
from opencore.browser.base import BaseView

def date_cmp(entry1, entry2):
    """compare feed entries by date"""
    return cmp(parse(entry1.date), parse(entry2.date))
        

class FeedView(BaseView):
    """view to render a feed in OC style"""
    
    def handle_request(self):

        uri = self.request.get('uri')
        n = self.request.get('n', 5)
                
        if uri:
            self.feed = feedparser.parse(uri)

            # these could be handled in a unified way
            try:
                title = self.feed.feed.title
            except AttributeError:
                # this means the uri is not a feed (or something?)
                delattr(self, 'feed')
                return
            self.title = self.request.get('title', title)
            self.subtitle = self.request.get('subtitle', self.title)

#            self.feed.entries.sort(cmp=date_cmp) # they appeared sorted already?
            self.feed.entries = self.feed.entries[:n]

