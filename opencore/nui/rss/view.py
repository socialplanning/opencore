import feedparser
from opencore.nui.base import BaseView

class RSSView(BaseView):
    def handle_request(self):
        self.title = 'Blog'
        uri = self.request.get('uri')
        if uri:
            self.feed = feedparser.parse(uri)
