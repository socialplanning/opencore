from zope.interface import implementer
from zope.component import adapter
from opencore.framework import IExtensibleContent
from opencore.project.browser.home_page import HomePageable, IHomePageable

@adapter(IExtensibleContent)
@implementer(IHomePageable)
def wiki_home_page(context):
    url = context.absolute_url() + '/' +  'project-home'
    return HomePageable('wiki', 'Pages', url)
from zope.component import getGlobalSiteManager
gsm = getGlobalSiteManager()
gsm.registerSubscriptionAdapter(wiki_home_page)

@adapter(IExtensibleContent)
@implementer(IHomePageable)
def summary_home_page(context):
    url = context.absolute_url() + '/' + 'latest-activity'
    return HomePageable('latest-activity', 'Summary', url)
gsm.registerSubscriptionAdapter(summary_home_page)
