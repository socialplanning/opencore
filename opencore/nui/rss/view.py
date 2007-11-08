import feedparser
from opencore.nui.base import BaseView

class RSSView(BaseView):
    def handle_request(self):
        uri = self.request.get('uri')
        if uri:
            self.feed = feedparser.parse(uri)
            self.title = self.request.get('title', self.feed.feed.title)
