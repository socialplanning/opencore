from opencore.utility.interfaces import IFeedbackerClient
from opencore.utility.interfaces import IHTTPClient
from opencore.utility.interfaces import IProvideSiteConfig
from zope.component import getUtility
from zope.interface import implements
import feedparser
import urlparse

class FeedbackerClient(object):
    """A global utility for making feedbacker requests"""
    implements(IFeedbackerClient)

    def get_atom(self, query_string):
        """Fetch an Atom feed from feedbacker using a GET request with
        the provided query string; parses the results w/ feedparser
        and returns the parsed feed object."""
        config = getUtility(IProvideSiteConfig)
        feedbacker_url = urlparse.urljoin(config.get('feedbacker uri'.strip()),
                                          config.get('feedbacker path'.strip()))
        req_url = "%satom?%s" % (feedbacker_url, query_string)
        h = getUtility(IHTTPClient)
        resp, content = h.request(req_url) # GET is the default
        if resp.get('status') != '200':
            # feedbacker failure
            return
        return feedparser.parse(content)
