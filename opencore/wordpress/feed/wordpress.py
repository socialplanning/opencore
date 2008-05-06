import feedparser
import urllib2

from opencore.feed.base import BaseFeedAdapter
from opencore.feed.base import FeedItemResponses
from opencore.feed.interfaces import IFeedData
from opencore.interfaces import IProject
from opencore.nui.wiki.utils import unescape # XXX this should not live here!
from zope.component import adapts
from zope.interface import implements

class WordpressFeedAdapter(BaseFeedAdapter):
    """feed for recent wordpress blogs"""
    # this should not be used if the project has no blog

    implements(IFeedData)
    adapts(IProject)

    title = 'Blog'
    itemstitle = 'blog posts'

    @property
    def link(self):
        return '%s/blog' % self.context.absolute_url()

    @property
    def items(self, n_items=5):
        if hasattr(self,'_items'):
            # If the property already contains something, there's no need to
            # regenerate it.
            return self._items

        # without the trailing slash, one gets different results!
        # see http://trac.openplans.org/openplans/ticket/2197#comment:3
        uri = '%s/blog/feed/' % self.context.absolute_url()

        # pull down the feed with the proper cookie
        req = urllib2.Request(uri)
        cookie = self.context.REQUEST.get_header('Cookie')
        if cookie:
            req.add_header('Cookie', cookie)
        try:
            feed = urllib2.urlopen(req).read()
        except urllib2.HTTPError:
            # fail silently for now
            feed = ''

        # parse with feedparser
        feed = feedparser.parse(feed)
        # feedparser takes care of HTML sanitization:
        # http://www.feedparser.org/docs/html-sanitization.html
        
        try:
            title = feed.feed.title
        except AttributeError:
            # this means the uri is not a feed (or something?)
            return []

        # maybe this should be done after comments?
        # feed.entries.sort(key=date_key) # they appeared sorted already?
        feed.entries = feed.entries[:n_items]

        for entry in feed.entries:
            n_comments = int(entry.get('slash_comments', 0))

            if n_comments:
                response = FeedItemResponses(n_comments,
                                             entry.comments,
                                             'comment')
            else:
                response=None

            title = entry.title
            if not title.strip():
                title = unescape(entry.summary) # XXX unescaping seems weird
                
            self.add_item(title=title,
                          description=entry.summary,
                          link=entry.link,
                          author=entry.author,
                          pubDate=entry.date,
                          responses=response)

        return self._items
