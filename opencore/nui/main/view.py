from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.viewlet.viewlet import ViewletBase
from opencore.project.utils import project_noun
from opencore.interfaces import IAmAPeopleFolder, IAddProject
from opencore.interfaces import IOpenSiteRoot

class SearchWidget(object):
    @property
    def project_noun(self):
        return project_noun()

    def current_search_page(self):
        if IAmAPeopleFolder.providedBy(self.context):
            return 'people'
        if IAddProject.providedBy(self.context):
            return 'projects'
        return 'sitesearch'

    def form_action_url(self):
        url = self.request.getURL()
        if IOpenSiteRoot.providedBy(self.context):
            return url
        else:
            return self.context.absolute_url() + '/searchresults'

class GetStarted(ViewletBase):
    render = ViewPageTemplateFile('get-started.pt')
    def project_noun(self):
        return project_noun()
