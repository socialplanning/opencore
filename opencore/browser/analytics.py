from Products.CMFPlone.utils import safe_unicode
from Products.Five.viewlet.viewlet import ViewletBase
from opencore.utility.interfaces import IProvideSiteConfig
from zope.component import getUtility

class AnalyticsSnippet(ViewletBase):
    """ include analytics engine JS snippet, if it exists in the
    site configuration """
    config_id ='analytics_snippet'
    
    def render(self):
        cfg = getUtility(IProvideSiteConfig)
        snippet = cfg.get(self.config_id, u'')
        if snippet:
            snippet = safe_unicode(snippet)
        return snippet
