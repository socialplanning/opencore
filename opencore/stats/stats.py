from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName
import DateTime



class StatsView(BrowserView):


    def get_projects(self)
        catalog = getToolByName(app.openplans, 'portal_catalog')
        query = dict(portal_type='OpenProject')
        brains = catalog(**query)

    def get_active_projects(self):    
        # "active" is defined as having been modified in the last 30 days

        projects = self.get_projects()
        filtered_projects = [project for project in projects if project.modified > DateTime.now()-.1]

        return filtered_projects
