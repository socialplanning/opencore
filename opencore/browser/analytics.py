from Products.CMFPlone.utils import safe_unicode
from Products.Five.viewlet.viewlet import ViewletBase
from opencore.interfaces.workflow import IReadWorkflowPolicySupport
from opencore.utility.interfaces import IProvideSiteConfig
from opencore.interfaces import IProject
from topp.utils.zutils import aq_iface
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


class GoogleAnalyticsSnippet(AnalyticsSnippet):
    """
    include a google analytics snippet for all pages except in closed
    projects
    """

    config_id = 'google_analytics_snippet'

    def render(self):
        proj = aq_iface(self.context, IProject)
        if proj is not None:
            proj_policy = IReadWorkflowPolicySupport(proj).getCurrentPolicyId()
            if proj_policy not in ('open_policy', 'medium_policy'):
                return u''
        return super(GoogleAnalyticsSnippet, self).render()
