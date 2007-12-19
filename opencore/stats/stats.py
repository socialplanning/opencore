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

        # do initial catalog queries
        query = dict()
        brains = self.membrane_tool(**query)
        self.members = brains
        query = dict(portal_type='OpenProject')
        brains = self.catalog(**query)
        self.projects = brains
        query = dict(portal_type='Open Mailing List')
        brains = self.catalog(**query)
        mailing_lists = brains
        mls = []
        for lst in mailing_lists:
            mail_catalog = queryUtility(ISearchableArchive, context=lst)
            latest_date = 0
            if mail_catalog:
                query = dict(sort_on='date',
                             sort_order='descending')
                brains = mail_catalog(**query)
                latest_date = brains[0].date
            if lst.modified > latest_date:
                latest_date = lst.modified
            mls.append({'Title':lst.Title,
                        'latest_date':latest_date,
                        'created':lst.created})
        self.mailing_lists = mls
            

    def get_active_members(self):    
        # "active" is defined as having logged in since expiry_date
        members = self.members
        filtered_members = []
        for mem in members:
            if mem.modified > self.expiry_date:
                filtered_members.append(mem)
        return filtered_members

    def get_unused_members(self):    
        # "unused" is defined as never using the account beyond the first 24 hours
        members = self.members
        filtered_members = []
        for mem in members:
            if (mem.modified - mem.created < 1) and (mem.modified < self.expiry_date):
                filtered_members.append(mem)
        return filtered_members

    def get_member_stickiness(self):
        # for all non-active members who were at one time active
        # find AVG(last_login - creation_date)
        # equals the average length of time a member is active
        members = self.members
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


    def get_active_projects(self):    
        # "active" is defined as having been modified since expiry_date
        # this includes wiki activity
        # this includes updating project prefs
        # does not include contents deletion
        # XXX what about including mailing list, tt, blog activity etc.
        projects = self.projects
        filtered_projects = [project for project in projects if project.modified > self.expiry_date]
        return filtered_projects

    def get_unused_projects(self):
        # "unused" is defined as having never been modified beyond the 
        # first 24 hours after it was created
        projects = self.projects
        filtered_projects = []
        for proj in projects:
            if (proj.modified < self.expiry_date) and (proj.modified - proj.created < 1):
                filtered_projects.append(proj)
        return filtered_projects
        

    def get_project_stickiness(self):
        # for all non-active projects which were at one time active
        # find AVG(modified - creation_date)
        # equals the average length of time a project is active
        projects = self.projects
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


    def get_active_mailing_lists(self):    
        # "active" is defined as having a message in the last 30 days
        filtered_lists = []
        for lst in self.mailing_lists:
            if lst['latest_date'] > self.expiry_date:
                filtered_lists.append(lst)
        return filtered_lists

    def get_unused_mailing_lists(self):
        # "unused" is defined as having never been used beyond the 
        # first 24 hours after it was created
        filtered_lists = []
        for lst in self.mailing_lists:
            if (lst['latest_date'] < self.expiry_date) and (lst['latest_date'] - lst['created'] < 1):
                filtered_lists.append(lst)
        return filtered_lists

        
