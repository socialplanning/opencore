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
        self.expiry_days = 30
        self.expiry_date = DateTime.now()-self.expiry_days

    def get_members(self):
        query = dict()
        brains = self.membrane_tool(**query)
        return brains

    def get_active_members(self):    
        # "active" is defined as having logged in since expiry_date
        members = self.get_members()
        filtered_members = []
        for mem in members:
            if mem.modified > self.expiry_date:
                filtered_members.append(mem)
        return filtered_members

    def get_unused_members(self):    
        # "unused" is defined as never using the account beyond the first 24 hours
        members = self.get_members()
        filtered_members = []
        for mem in members:
            if (mem.modified - mem.created < 1) and (mem.modified < self.expiry_date):
                filtered_members.append(mem)
        return filtered_members

    def get_member_stickiness(self):
        # for all non-active members who were at one time active
        # find AVG(last_login - creation_date)
        # equals the average length of time a member is active
        members = self.get_members()
        active_length = 0
        i = 0
        for mem in members:
            if (mem.modified < self.expiry_date) and (mem.modified - mem.created >= 1):
                i += 1
                active_length += mem.modified - mem.created
        
        if i > 0:
            avg_active_length = active_length / i
        else:
            avg_active_length = 0
        return avg_active_length, i


    def get_projects(self):
        query = dict(portal_type='OpenProject')
        brains = self.catalog(**query)
        return brains

    def get_active_projects(self):    
        # "active" is defined as having been modified since expiry_date
        # this includes wiki activity
        # this includes updating project prefs
        # does not include contents deletion
        # XXX what about including mailing list, tt, blog activity etc.
        projects = self.get_projects()
        filtered_projects = [project for project in projects if project.modified > self.expiry_date]
        return filtered_projects

    def get_unused_projects(self):
        # "unused" is defined as having never been modified beyond the 
        # first 24 hours after it was created
        projects = self.get_projects()
        filtered_projects = []
        for proj in projects:
            if (proj.modified < self.expiry_date) and (proj.modified - proj.created < 1):
                filtered_projects.append(proj)
        return filtered_projects
        

    def get_project_stickiness(self):
        # for all non-active projects which were at one time active
        # find AVG(modified - creation_date)
        # equals the average length of time a project is active
        projects = self.get_projects()
        active_length = 0
        i = 0
        for proj in projects:
            if (proj.modified < self.expiry_date) and (proj.modified - proj.created >= 1):
                i += 1
                active_length += proj.modified - proj.created
        
        if i > 0:
            avg_active_length = active_length / i
        else:
            avg_active_length = 0
        return avg_active_length, i




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
            if latest_date > self.expiry_date:
                filtered_lists.append(lst)
        
        return filtered_lists


        
