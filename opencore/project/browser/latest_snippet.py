from topp.utils.pretty_date import prettyDate

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class LatestSnippet(BrowserView):

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)

        self.feedtitle = 'title'
        self.link = 'http://www.google.com'
        self.items = []

    def pretty_date(self, date):
        # XXX this is copy/pasted
        return prettyDate(date)

