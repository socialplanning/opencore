"""
Naked Base View
"""
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from memojito import memoizedproperty, memoize
from opencore import redirect 
from opencore.interfaces import IProject 
from topp.utils.pretty_date import prettyDate
from zope.component import getMultiAdapter, adapts, adapter

class NakedView(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.transclude = request.get_header('X-transcluded')

    def include(self, view):
        if self.transclude:
            return '<a href="@@%s" rel="include">%s</a>' % (view, view)
        else:
            return self.context.unrestrictedTraverse('@@' + view).index()
