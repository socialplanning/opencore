from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class LatestSnippet(BrowserView):

#    template = ZopeTwoPageTemplateFile('latest_snippet.pt')
    
    def __init__(self, context, request, title):
        BrowserView.__init__(self, context, request)

        self.feedtitle = title
        self.items = []
#        import pdb;  pdb.set_trace()

    def __call__(self):
        import pdb; pdb.set_trace()
        return 'fggggg'
        ViewPageTemplateFile('latest_snippet.pt')
