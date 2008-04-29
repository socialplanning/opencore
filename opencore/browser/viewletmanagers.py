from Products.Five.viewlet.manager import ViewletManagerBase
from opencore.browser.interfaces import IJSViewlets

from zope.interface import implements

class SortedViewletManager(ViewletManagerBase):

    def sort(self, viewlets):
        """Sort the viewlets according to their sort_order attribute"""
        try:
            return sorted(viewlets, key=lambda x:int(x[1].sort_order))
        except AttributeError:
            import pdb; pdb.set_trace()
            

class JSViewletManager(SortedViewletManager):
    """sorted viewlet manager for project-related javascript """

    implements(IJSViewlets)
