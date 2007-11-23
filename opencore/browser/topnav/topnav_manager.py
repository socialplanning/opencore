from zope.viewlet.manager import ViewletManagerBase

class SortingViewletManager(ViewletManagerBase):
    #XXX not being used because
    # setting this as the viewlet manager class
    # was raising security errors
    # instead, the viewlets implement the __cmp__ method
    # which is how they are sorted by default
    def sort(self, viewlets):
        return sorted(viewlets)
