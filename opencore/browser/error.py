from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName

from opencore.browser.base import BaseView

class ErrorView(BaseView):

    notfound = ZopeTwoPageTemplateFile('notfound.pt')
    error = ZopeTwoPageTemplateFile('error.pt')

    def find_name(self):
        """ this is really dumb. there must be a better way. """
        return self.request.getURL().split('/')[-1]

    def query(self):
        name = self.find_name()
        cat = getToolByName(self.context, 'portal_catalog')
        results = cat(path='/'.join(self.context.getPhysicalPath()), SearchableText=name)
        return results

    def __call__(self, *args, **kw):
        if kw['error_type'] == 'NotFound':
            return self.notfound(*args, **kw)
        return self.error(*args, **kw)
