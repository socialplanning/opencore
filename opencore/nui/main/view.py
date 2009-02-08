from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.viewlet.viewlet import ViewletBase
from opencore.project.utils import project_noun

class WithProjectNoun(object):
    @property
    def project_noun(self):
        return project_noun()

    def current_search_page(self):
        url = self.request.getURL()
        if url.endswith('searchresults'):
            url = url.split('/')[-2]
        else:
            url = url.split('/')[-1]
        return url

class GetStarted(ViewletBase):
    render = ViewPageTemplateFile('get-started.pt')
    def project_noun(self):
        return project_noun()
