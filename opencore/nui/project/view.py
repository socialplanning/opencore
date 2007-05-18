from opencore.nui.opencoreview import OpencoreView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName

class ProjectView(OpencoreView):
    project_preferences = ZopeTwoPageTemplateFile('project-preferences.pt')
    project_create = ZopeTwoPageTemplateFile('project-create.pt')

    def updateProject(self):
        return self.project_preferences()

    def createProject(self):
        return self.project_create()

    def doUpdateProject(self):
        proj = self.context
        proj.setFull_name(self.request.get('fullname'))
        proj.setDescription(self.request.get('mission'))
        self.request.response.redirect(proj.absolute_url())
