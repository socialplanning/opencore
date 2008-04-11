from Products.Five.viewlet.manager import ViewletManagerBase
from opencore.project.browser.interfaces import ISummaryFeeds
from zope.interface import implements

class SummaryManager(ViewletManagerBase):
    """custom viewlet manager for summary items"""

    implements(ISummaryFeeds)

    def sort(self, viewlets):
        """Sort the viewlets according to their sort_order attribute"""
        return sorted(viewlets, key=lambda x:int(x[1].sort_order))
