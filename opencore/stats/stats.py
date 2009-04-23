from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.listen.interfaces import ISearchableArchive
from opencore.testing.utils import clear_all_memos
from opencore.utils import get_utility_for_context
from plone.memoize import view
import DateTime
import opencore.project.utils

class StatsView(BrowserView):
    # Note: by passing in report_date you can get stats for the portal as of
    # any previous date.  These aren't, however, exactly what you would get
    # if you were to run the stats on that date.  For example, people who
    # were dormant during a certain period but then become active again
    # would show up as active if you set report_date for the dormant period.
    # If you had run the stats during that dormant period they would show
    # up as dormant.  The same goes for mailing lists and projects that go through
    # a dormant period and then become active again.


    menu = ZopeTwoPageTemplateFile('menu.pt')

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.catalog = getToolByName(self.context, 'portal_catalog')
        self.membrane_tool = getToolByName(self.context, 'membrane_tool')
        self.expiry_days = 30
        r_date = getattr(self.request, 'report_date', None)
        if r_date:
            self.report_date = DateTime.DateTime(r_date)
        else:
            self.report_date = DateTime.now()
        self.expiry_date = self.report_date-self.expiry_days        

    @view.memoize_contextless
    def get_members(self):
        query = {}
        mem_brains = self.membrane_tool(**query)
        return [brain for brain in mem_brains if brain.created <= self.report_date]
    

    @view.memoize_contextless
    def get_projects(self):
        query = dict(portal_type='OpenProject')
        proj_brains = self.catalog(**query)
        return [brain for brain in proj_brains if brain.created <= self.report_date]

    @view.memoize_contextless
    def get_mailing_lists(self, path=None):
        query = dict(portal_type='Open Mailing List')
        if path:
            query['path'] = path
        ml_brains = self.catalog(**query)
        mailing_lists = [brain for brain in ml_brains if brain.created <= self.report_date]
        mls = []
        for lst in mailing_lists:
            mail_catalog = get_utility_for_context(ISearchableArchive,
                                                   context=lst.getObject())
            latest_date = DateTime.DateTime(0)
            if mail_catalog:
                query = dict(sort_on='date',
                             sort_order='descending')
                brains = mail_catalog(**query)
                latest_date = brains[0].date
            mls.append({'Title':lst.Title,
                        'latest_date':latest_date,
                        'created':lst.created,
                        'num_threads': lst.mailing_list_threads,
                        })
        return mls
            

    @view.memoize_contextless
    def get_active_members(self):    
        # "active" is defined as having logged in since expiry_date
        # it does not include posts to or receipts from a mailing list
        filtered_members = [mem for mem in self.get_members()
                            if mem.modified > self.expiry_date]
        return filtered_members

    @view.memoize_contextless
    def get_unused_members(self):    
        # "unused" is defined as never using the account beyond the
        # first 24 hours
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

    @view.memoize_contextless
    def get_active_projects(self):    
        # "active" is defined as having been modified since expiry_date
        # this includes wiki activity
        # this includes updating project prefs
        # does not include contents deletion
        # XXX what about including mailing list, tt, blog activity etc.
        filtered_projects = [project for project in self.get_projects()
                             if project.modified > self.expiry_date]
        return filtered_projects


    @view.memoize_contextless
    def get_active_projects_info(self, select='active'):
        if select == 'active':
            brains = self.get_active_projects()
        else:
            brains = self.get_projects()
        info = [self.get_info_for_project(brain) for brain in brains]
        return info

    def get_info_for_project(self, brain):
        """ Info for one project."""
        proj = brain.getObject()
        proj_last_updated = brain.modified
        num_members = len(proj.projectMemberIds())
        #num_admins = len(proj.projectMemberIds(admin_only=True))
        # We need the whole thing, might as well listify it.
        _page_brains = list(self.catalog(
                                    path=brain.getPath(), #XXX borken
                                    portal_type='Document',
                                    sort_on='ModificationDate',
                                    sort_order='descending',
                                    sort_limit=1))
        if _page_brains:
            last_wiki_edit = _page_brains[-1].modified
        else:
            last_wiki_edit = ''
        num_wiki_pages = len(_page_brains)

        date_of_last_thread = ''
        num_threads = 0
        lists = self.get_mailing_lists(path=brain.getPath() + '/lists/')
        if lists:
            date_of_last_thread = DateTime.DateTime(0)
        for listinfo in lists:
            date_of_last_thread = max(date_of_last_thread, listinfo['latest_date'])
            num_threads += listinfo['num_threads']

        proj_last_updated = max(proj_last_updated, last_wiki_edit,
                                date_of_last_thread)

        return {'num_threads': num_threads, 
                'date_of_last_thread': date_of_last_thread,
                'last_wiki_edit': last_wiki_edit,
                'num_wiki_pages': num_wiki_pages,
                #'num_admins': num_admins,
                'num_members': num_members,
                'last_activity': proj_last_updated,
                'id': brain.getId,
                'path': brain.getPath(),
                }
        # XXX This stuff will take more work:
        featurelets = opencore.project.utils.get_featurelets(proj)
        # num blog posts (optional)
        # date of last blog post (optional)
        # num tasks (optional)
        # date of last task edit (optional)


    @view.memoize_contextless
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

    @view.memoize_contextless
    def get_active_mailing_lists(self):    
        # "active" is defined as having a message in the last 30 days
        filtered_lists = []
        for lst in self.get_mailing_lists():
            if lst['latest_date'] > self.expiry_date:
                filtered_lists.append(lst)
        return filtered_lists

    @view.memoize_contextless
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
        # this is only useful for approximations of general trends in the past
        # it is not a very accurate way to get historical stats
        data = []
        initial_report_date = self.report_date
        for i in range(0, 18):
            self.report_date = initial_report_date - i*30
            clear_all_memos(self)
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
