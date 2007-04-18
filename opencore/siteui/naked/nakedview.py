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
        self.sitetitle = 'OpenPlans' # TODO make more generic
        self.piv = context.unrestrictedTraverse('project_info') # TODO make more generic
        self.miv = context.unrestrictedTraverse('member_info') # TODO make more generic

    def _transclude(self):
        return self.request.get_header('X-transcluded')

    def include(self, view):
        if self._transclude():
            return '<a href="%s" rel="include">%s</a>' % (view, view)
        return self.context.unrestrictedTraverse(view).index()

    def _title_info(self):
        if self.piv.inProject:
            title = self.piv.fullname
            subtitle = self.context.title
        elif self.miv.inMemberArea:
            title = self.miv.membername
            subtitle = 'foo'
        else:
            title = self.context.title
            subtitle = 'bar'
        return title, subtitle

    def renderWindowTitle(self):
        title, subtitle = self._title_info()
        title, subtitle = truncate(title, max=16), truncate(subtitle, max=24)
        windowtitle = [subtitle, title, self.sitetitle]
        return ' :: '.join([i for i in windowtitle if i])

    def renderTopnavTitle(self):
        title, _ = self._title_info()
        title = truncate(title, max=64)
        h1 = '<h1>%s</h1>' % title
        return '<a href="%s">%s</a>' % (self.context.absolute_url(), h1)

    def renderPageTitle(self):
        _, subtitle = self._title_info()
        subtitle = truncate(subtitle, max=256)
        return '<a href="%s">%s</a>' % (self.context.absolute_url(), subtitle)
