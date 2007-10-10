from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName
import DateTime
from Products.listen.interfaces import ISearchableArchive
from zope.component import queryUtility


class StatsView(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.catalog = getToolByName(self.context, 'portal_catalog')
        self.membrane_tool = getToolByName(self.context, 'membrane_tool')
        

    def get_projects(self):
        query = dict(portal_type='OpenProject')
        brains = self.catalog(**query)
        return brains

    def get_active_projects(self):    
        # "active" is defined as having been modified in the last 30 days
        projects = self.get_projects()
        filtered_projects = [project for project in projects if project.modified > DateTime.now()-30]
        return filtered_projects

    def get_members(self):
        query = dict()
        brains = self.membrane_tool(**query)
        return brains

    def get_active_members(self):    
        # "active" is defined as having logged in the last 30 days
        members = self.get_members()
        filtered_members = [member for member in members if member.modified > DateTime.now()-30]
        return filtered_members

    def get_mailing_lists(self):
        query = dict(portal_type='Open Mailing List')
        brains = self.catalog(**query)
        return brains

    def get_active_mailing_lists(self):    
        # "active" is defined as having a message in the last 30 days
        lists = self.get_mailing_lists()
        filtered_lists = []
        for lst in lists:
            mail_catalog = queryUtility(ISearchableArchive, context=lst)
            latest_date = 0
            if mail_catalog:
                query = dict(sort_on='date',
                             sort_order='descending')
                brains = mail_catalog(**query)
                latest_date = brains[0].date
            if lst.modified > latest_date:
                latest_date = lst.modified
            if latest_date > DateTime.now()-30:
                filtered_lists.append(lst)
        
        return filtered_lists

    


        
