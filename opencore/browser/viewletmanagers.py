from Products.Five.viewlet.manager import ViewletManagerBase
from opencore.browser.interfaces import IJSViewlets

from zope.interface import implements

class SortedViewletManager(ViewletManagerBase):

    def sort(self, viewlets):
        """Sort the viewlets according to their sort_order attribute"""
        return sorted(viewlets, key=lambda x:int(x[1].sort_order))

    
class JSViewletManager(SortedViewletManager):
    """sorted viewlet manager for project-related javascript """

    implements(IJSViewlets)
