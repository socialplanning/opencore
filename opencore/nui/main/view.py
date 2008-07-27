from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.viewlet.viewlet import ViewletBase
from opencore.project.utils import project_noun

class GetStarted(ViewletBase):

    def project_noun(self):
        return project_noun()
