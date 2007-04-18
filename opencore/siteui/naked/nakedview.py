"""
Naked Base View
"""
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from memojito import memoizedproperty, memoize
from opencore import redirect 
from opencore.interfaces import IProject 
from topp.utils.pretty_date import prettyDate
from topp.utils.pretty_text import truncate
from zope.component import getMultiAdapter, adapts, adapter

class NakedView(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.transclude = request.get_header('X-transcluded')
        self.piv = self.context.unrestrictedTraverse('project_info')
        self.miv = self.context.unrestrictedTraverse('member_info')

    def include(self, view):
        if self.transclude:
            return '<a href="%s" rel="include">%s</a>' % (view, view)
        return self.context.unrestrictedTraverse(view).index()

    def _title_info(self):
        if self.piv.inProject:
            title = self.piv.fullname
            url = self.piv.url
        elif self.miv.inMemberArea:
            title = self.miv.membername
            url = self.miv.url
        else:
            title = self.context.title
            url = None
        return title, url

    def renderPageTitle(self):
        title, _ = self._title_info()
        title = truncate(title)
        return '%s :: OpenPlans' % title

    def renderTopnavTitle(self):
        title, url = self._title_info()
        title = truncate(title, max=64)
        h1 = '<h1>%s</h1>' % title
        return '<a href="%s">%s</a>' % (url, h1)
