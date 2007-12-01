from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile



class LatestSnippet(BrowserView):

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)

        self.feedtitle = 'title'
        self.items = []

