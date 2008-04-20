from Products.Five.viewlet.manager import ViewletManagerBase
from opencore.project.browser.interfaces import ISummaryFeeds
from opencore.project.browser.interfaces import IProjectPrefs

from zope.interface import implements

class SortedViewletManager(ViewletManagerBase):

    def sort(self, viewlets):
        """Sort the viewlets according to their sort_order attribute"""
        return sorted(viewlets, key=lambda x:int(x[1].sort_order))

class SummaryManager(SortedViewletManager):
    """custom viewlet manager for summary items"""

    implements(ISummaryFeeds)

class ProjectPrefsManager(SortedViewletManager):
    """ custom viewlet manager for project preferences """

    implements(IProjectPrefs)
