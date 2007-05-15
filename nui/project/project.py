from opencore.nui.opencoreview import OpencoreView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName

class ProjectView(OpencoreView):
    project_preferences = ZopeTwoPageTemplateFile('project-preferences.pt')

    def updateProject(self):
        return self.project_preferences()

    def createProject(self):
        return self.project_preferences()
