from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from opencore.utility.interfaces import IFeedbackerClient
from opencore.utility.interfaces import IHTTPClient
from opencore.utility.interfaces import IProvideSiteConfig
from topp.utils.zutils import aq_iface
from zope.app.component.hooks import getSite
from zope.component import getUtility
from zope.interface import implements
import feedparser
import urlparse

class FeedbackerClient(object):
    """A global utility for making feedbacker requests"""
    implements(IFeedbackerClient)

    def get_atom(self, query_string, send_auth=False):
        """Fetch an Atom feed from feedbacker using a GET request with
        the provided query string; parses the results w/ feedparser
        and returns the parsed feed object."""
        config = getUtility(IProvideSiteConfig)
        feedbacker_url = urlparse.urljoin(config.get('feedbacker uri'.strip()),
                                          config.get('feedbacker path'.strip()))
        req_url = "%satom?%s" % (feedbacker_url, query_string)
        h = getUtility(IHTTPClient)

        context = getSite()
        mship_tool = getToolByName(context, 'portal_membership')
        headers = {}
        if send_auth and not mship_tool.isAnonymousUser():
            member = mship_tool.getAuthenticatedMember()
            login = member.id
            auth_helper = self._get_auth_helper(context)
            cookie = auth_helper.generateCookie(login)
            headers = dict(Cookie=cookie)

        resp, content = h.request(req_url,
                                  method="GET",
                                  headers=headers,
                                  )
        if resp.get('status') != '200':
            # feedbacker failure
            return
        return feedparser.parse(content)

    def _get_auth_helper(self, context):
        portal = aq_iface(context, IPloneSiteRoot)
        return portal.acl_users.credentials_signed_cookie_auth
