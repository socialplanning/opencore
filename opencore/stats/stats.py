from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName
import DateTime
from Products.listen.interfaces import ISearchableArchive
from zope.component import queryUtility


class StatsView(BrowserView):
    # Note: by passing in report_date you can get stats for the portal as of
    # any previous date.  These aren't, however, exactly what you would get
    # if you were to run the stats on that date.  For example, people who
    # were dormant during a certain period but then become active again
    # would show up as active if you set report_date for the dormant period.
    # If you had run the stats during that dormant period they would show
    # up as dormant.  The same goes for mailing lists and projects that go through
    # a dormant period and then become active again.
    # However, I believe these are rare cases and should only have
    # a negligible effect on the historical stats.  This, also, is the best
    # we can do with the given bits of information.

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.catalog = getToolByName(self.context, 'portal_catalog')
        self.membrane_tool = getToolByName(self.context, 'membrane_tool')
        self.expiry_days = 30
        self.ran_queries = False
        r_date = getattr(self.request, 'report_date', None)
        if r_date:
            self.report_date = DateTime.DateTime(r_date)
        else:
            self.report_date = DateTime.now()


    def _init_queries(self):
        # do initial catalog queries
        if self.ran_queries:
            return

        self.ran_queries = True
        self.expiry_date = self.report_date-self.expiry_days        

        query = dict()
        mem_brains = self.membrane_tool(**query)
        self._members = [brain for brain in mem_brains if brain.created <= self.report_date]
        query = dict(portal_type='OpenProject')
        proj_brains = self.catalog(**query)
        self._projects = [brain for brain in proj_brains if brain.created <= self.report_date]
        query = dict(portal_type='Open Mailing List')
        ml_brains = self.catalog(**query)
        mailing_lists = [brain for brain in ml_brains if brain.created <= self.report_date]
        mls = []
        self.mod_date_used = 0
        for lst in mailing_lists:
            mail_catalog = queryUtility(ISearchableArchive, context=lst.getObject())
            latest_date = 0
            if mail_catalog:
                query = dict(sort_on='date',
                             sort_order='descending')
                brains = mail_catalog(**query)
                latest_date = brains[0].date
            if lst.modified > latest_date:
                latest_date = lst.modified
                self.mod_date_used += 1
            mls.append({'Title':lst.Title,
                        'latest_date':latest_date,
                        'created':lst.created})
        self._mailing_lists = mls
            
    def get_report_date(self):
        self._init_queries()
        return self.report_date        

    def get_members(self):
        self._init_queries()
        return self._members

    def get_active_members(self):    
        # "active" is defined as having logged in since expiry_date
        # it does not include posts to or receipts from a mailing list
        filtered_members = []
        for mem in self.get_members():
            if mem.modified > self.expiry_date:
                filtered_members.append(mem)
        return filtered_members

    def get_unused_members(self):    
        # "unused" is defined as never using the account beyond the first 24 hours
        filtered_members = []
        for mem in self.get_members():
            if (mem.modified - mem.created < 1) and (mem.modified < self.expiry_date):
                filtered_members.append(mem)
        return filtered_members

    def get_member_stickiness(self):
        # for all non-active members who were at one time active
        # find AVG(last_login - creation_date)
        # equals the average length of time a member is active
        active_length = 0
        i = 0
        for mem in self.get_members():
            if (mem.modified < self.expiry_date) and (mem.modified - mem.created >= 1):
                i += 1
                active_length += mem.modified - mem.created
        
        if i > 0:
            avg_active_length = active_length / i
        else:
            avg_active_length = 0
        return i, avg_active_length

    def get_projects(self):
        self._init_queries()
        return self._projects

    def get_active_projects(self):    
        # "active" is defined as having been modified since expiry_date
        # this includes wiki activity
        # this includes updating project prefs
        # does not include contents deletion
        # XXX what about including mailing list, tt, blog activity etc.
        filtered_projects = [project for project in self.get_projects() if project.modified > self.expiry_date]
        return filtered_projects

    def get_unused_projects(self):
        # "unused" is defined as having never been modified beyond the 
        # first 24 hours after it was created
        filtered_projects = []
        for proj in self.get_projects():
            if (proj.modified < self.expiry_date) and (proj.modified - proj.created < 1):
                filtered_projects.append(proj)
        return filtered_projects
        

    def get_project_stickiness(self):
        # for all non-active projects which were at one time active
        # find AVG(modified - creation_date)
        # equals the average length of time a project is active
        active_length = 0
        i = 0
        for proj in self.get_projects():
            if (proj.modified < self.expiry_date) and (proj.modified - proj.created >= 1):
                i += 1
                active_length += proj.modified - proj.created
        
        if i > 0:
            avg_active_length = active_length / i
        else:
            avg_active_length = 0
        return i, avg_active_length

    def get_mailing_lists(self):
        self._init_queries()
        return self._mailing_lists

    def get_active_mailing_lists(self):    
        # "active" is defined as having a message in the last 30 days
        filtered_lists = []
        for lst in self.get_mailing_lists():
            if lst['latest_date'] > self.expiry_date:
                filtered_lists.append(lst)
        return filtered_lists

    def get_unused_mailing_lists(self):
        # "unused" is defined as having never been used beyond the 
        # first 24 hours after it was created
        filtered_lists = []
        for lst in self.get_mailing_lists():
            if (lst['latest_date'] < self.expiry_date) and (lst['latest_date'] - lst['created'] < 1):
                filtered_lists.append(lst)
        return filtered_lists

    def get_mailing_list_stickiness(self):
        # for all non-active lists which were at one time active
        # find AVG(latest_date - creation_date)
        # equals the average length of time a list is active
        active_length = 0
        i = 0
        for lst in self.get_mailing_lists():
            if (lst['latest_date'] < self.expiry_date) and (lst['latest_date'] - lst['created'] >= 1):
                i += 1
                active_length += lst['latest_date'] - lst['created']
        
        if i > 0:
            avg_active_length = active_length / i
        else:
            avg_active_length = 0
        return i, avg_active_length
        

    def get_active_data(self):
        data = []
        initial_report_date = self.report_date
        for i in range(0, 18):
            self.report_date = initial_report_date - i*30
            self.ran_queries = False
            self._init_queries()
            data.append({'date':self.report_date,
                         'members':len(self.get_active_members()),
                         'members_life':self.get_member_stickiness()[1],
                         'projects':len(self.get_active_projects()),
                         'projects_life':self.get_project_stickiness()[1],
                         'mailing_lists':len(self.get_active_mailing_lists()),
                         'mailing_lists_life':self.get_mailing_list_stickiness()[1]})

        self.report_date = initial_report_date
        self.ran_queries = False
        return data
