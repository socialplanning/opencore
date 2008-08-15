from opencore.project.browser.interfaces import ISummaryFeeds
from opencore.browser.viewletmanagers import SortedViewletManager
from zope.interface import implements

class SummaryManager(SortedViewletManager):
    """custom viewlet manager for summary items"""

    implements(ISummaryFeeds)

