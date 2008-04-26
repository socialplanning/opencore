from AccessControl.ZopeGuards import guarded_hasattr
from Acquisition import aq_inner
from Products.Five.viewlet.manager import ViewletManagerBase
from opencore.browser.interfaces import IJSViewlets

from zope.interface import implements

class SortedViewletManager(ViewletManagerBase):

    def filter(self, viewlets):
        """Sort out all content providers

        ``viewlets`` is a list of tuples of the form (name, viewlet).

        use the physical path's acquisition context.
        """
        results = []
        # Only return viewlets accessible to the principal
        # We need to wrap each viewlet in its context to make sure that
        # the object has a real context from which to determine owner
        # security.
        for name, viewlet in viewlets:
            viewlet = viewlet.__of__(aq_inner(viewlet.context))
            if guarded_hasattr(viewlet, 'render'):
                results.append((name, viewlet))
        return results

    def sort(self, viewlets):
        """Sort the viewlets according to their sort_order attribute"""
        return sorted(viewlets, key=lambda x:int(x[1].sort_order))

class JSViewletManager(SortedViewletManager):
    """sorted viewlet manager for project-related javascript """

    implements(IJSViewlets)
