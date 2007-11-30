import feedparser
from opencore.browser.base import BaseView

class FeedView(BaseView):
    def handle_request(self):
        uri = self.request.get('uri')
        if uri:
            self.feed = feedparser.parse(uri)
            self.title = self.request.get('title', self.feed.feed.title)
