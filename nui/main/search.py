import datetime
from DateTime import DateTime as zopedatetime
from time import strptime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import Batch
from Products.AdvancedQuery import Eq, RankByQueries_Sum
from topp.utils.pretty_date import prettyDate
from zExceptions import Redirect 
from opencore.nui.opencoreview import OpencoreView


class SearchView(OpencoreView):

    def _get_batch(self, brains, start=0):
        return Batch(brains,
                     size=10,
                     start=start,
                     end=0,
                     orphan=0,
                     overlap=0,
                     pagerange=6,
                     quantumleap=0,
                     b_start_str='b_start')

    def create_sort_fn(self, sort_by):

        def sort_key_fn(x):
            if sort_by is None or sort_by == 'relevancy': return 0
            
            prop = getattr(x, sort_by)
            if callable(prop):
                return prop()
            return prop

        return sort_key_fn

    def pretty_date(self, date):
        try:
            time_obj = strptime(date, '%Y-%m-%d %H:%M:%S')
            datetime_obj = datetime.datetime(*time_obj[0:6])
        except TypeError:
            datetime_obj = date
        return prettyDate(datetime_obj)



class ProjectsSearchView(SearchView):

    def __call__(self):
        projname = self.request.get('projname', None)
        letter_search = self.request.get('letter_search', None)
        start = self.request.get('b_start', 0)
        sort_by = self.request.get('sort_by', None)
        self.search_results = None
        self.search_query = None

        # this resets pagination when the sort order is changed
        if self.request.get('REQUEST_METHOD', None) == 'POST':
            start = 0
            self.request.set('b_start', 0)
            
        if letter_search:
            self.search_results = self._get_batch(self.search_for_project_by_letter(letter_search, sort_by), start)
            self.search_query = 'for projects starting with &ldquo;%s&rdquo;' % letter_search
        elif projname:
            self.search_results = self._get_batch(self.search_for_project(projname, sort_by), start)
            self.search_query = 'for &ldquo;%s&rdquo;' % projname
            
        return self.index()
            
    def search_for_project_by_letter(self, letter, sort_by=None):
        letter = letter.lower()
        query = dict(portal_type="OpenProject",
                     Title=letter + '*')
        project_brains = self.catalogtool(**query)

        def matches(brain):
            title = brain.Title.lower()
            return title.startswith(letter) \
                or title.startswith('the ' + letter) \
                or title.startswith('a ' + letter) \
                or title.startswith('an ' + letter)

        project_brains = filter(matches, project_brains)

        project_brains.sort(key=self.create_sort_fn(sort_by))

        return project_brains

    def search_for_project(self, project, sort_by=None):
        proj_query = project.lower().strip()

        if proj_query == '*':
            return []
        if not proj_query.endswith('*'):
            proj_query = proj_query + '*'

        if not sort_by or sort_by == 'relevancy':
            rs = (RankByQueries_Sum((Eq('Title', proj_query),32), (Eq('getFull_name', proj_query),16)),)
        else:
            # we can't sort by title
            if sort_by == 'Title':
                sort_by = 'sortable_title'
            rs = ((sort_by, 'desc'),)

        project_brains = self.catalogtool.evalAdvancedQuery(
            Eq('portal_type', 'OpenProject') & Eq('SearchableText', proj_query),
            rs,
            )
        return project_brains
    
    def recently_updated_projects(self):
        # XXX
        # This is not exactly what we want
        # These get all modifications on the project itself
        # but will miss wiki page changes in the project
        # which is the sort of thing you would expect here
        query = dict(portal_type='OpenProject',
                     sort_on='modified',
                     sort_order='descending',
                     sort_limit=5,
                     )

        project_brains = self.catalogtool(**query) 
        # XXX expensive $$$
        # we get object for number of project members
        projects = (x.getObject() for x in project_brains)
        return projects


class PeopleSearchView(SearchView):
    def __init__(self, context, request):
        SearchView.__init__(self, context, request)
        self.membrane_tool = getToolByName(context, 'membrane_tool')

    def __call__(self):
        personname = self.request.get('personname', None)
        letter_search = self.request.get('letter_search', None)
        start = self.request.get('b_start', 0)
        sort_by = self.request.get('sort_by', None)
        self.search_results = None
        self.search_query = None

        # this resets pagination when the sort order is changed
        if self.request.get('REQUEST_METHOD', None) == 'POST':
            start = 0
            self.request.set('b_start', 0)
            
        if letter_search:
            self.search_results = self._get_batch(self.search_for_person_by_letter(letter_search, sort_by), start)
            self.search_query = 'for members starting with &ldquo;%s&rdquo;' % letter_search
        elif personname:
            self.search_results = self._get_batch(self.search_for_person(personname, sort_by), start)
            self.search_query = 'for &ldquo;%s&rdquo;' % personname
            
        return self.index()

    def search_for_person_by_letter(self, letter, sort_by=None):
        letter = letter.lower()
        query = dict(Title=letter + '*')
        people_brains = self.membrane_tool(**query)

        people_brains = sorted(people_brains, key=self.create_sort_fn(sort_by))

        return people_brains

    def search_for_person(self, person, sort_by=None):
        person_query = person.lower().strip()

        if person_query == '*':
            return []

        if not person_query.endswith('*'):
            person_query = person_query + '*'

        if not sort_by or sort_by == 'relevancy':
            rs = (RankByQueries_Sum((Eq('Title', person_query),32), (Eq('getId', person_query),16)),)
        else:
            # we can't sort by title
            if sort_by == 'Title':
                sort_by = 'exact_getFullname'
            rs = ((sort_by, 'desc'),)

        people_brains = self.membrane_tool.evalAdvancedQuery(
            Eq('RosterSearchableText', person_query),
            rs,
            )
        return people_brains

    def no_home(self, userid):
        """ check to see if a user has a people folder (has logged in)
            note: not using mtool.getHomeFolder for efficiency reasons """
        return not self.context.has_key(userid)


class HomeView(SearchView):
    def __init__(self, context, request):
        SearchView.__init__(self, context, request)
        self.projects_search = ProjectsSearchView(context, request)

    def __call__(self):
        go_here = self.request.get('go_here', None)

        if go_here:
            raise Redirect, go_here
        
        return self.index()


    def recently_updated_projects(self):
        return self.projects_search.recently_updated_projects()

    def recently_created_projects(self):
        query = dict(portal_type='OpenProject',
                     sort_on='Creator',
                     sort_order='descending',
                     sort_limit=5,
                     )

        project_brains = self.catalogtool(**query) 
        # XXX expensive $$$
        # we get object for number of project members
        projects = (x.getObject() for x in project_brains)
        return projects

    def news(self):
        news_path = '/'.join(self.context.portal.getPhysicalPath()) + '/news'
        query = dict(portal_type='Document',
                     sort_on='created',
                     sort_order='descending',
                     sort_limit=4,
                     path=news_path
                     )
        brains = self.catalogtool(**query)
        return brains
        


class SitewideSearchView(SearchView):

    def __call__(self):
        search_string = self.request.get('search_string', None)
        search_action = self.request.get('search_action', None)
        start = self.request.get('b_start', 0)
        sort_by = self.request.get('sort_by', None)
        self.search_results = None
        self.search_query = None

        # this resets pagination when the sort order is changed
        if self.request.get('REQUEST_METHOD', None) == 'POST':
            start = 0
            self.request.set('b_start', 0)
            
        if search_string:
            self.search_results = self._get_batch(self.search(search_string, sort_by), start)
            self.search_query = 'for &ldquo;%s&rdquo;' % search_string
            
        return self.index()
            

    def search(self, search_string, sort_by=None):
        search_query = search_string.lower().strip()

        if search_query == '*':
            return []

        if not search_query.endswith('*'):
            search_query = search_query + '*'

        if not sort_by or sort_by == 'relevancy':
            rs = (RankByQueries_Sum((Eq('getId', search_query),32), (Eq('getFull_name', search_query),16)),)
        else:
            # we can't sort by title
            if sort_by == 'getId':
                rs = ((sort_by, 'asc'),)
            else:
                rs = ((sort_by, 'desc'),)

        brains = self.catalogtool.evalAdvancedQuery(
            (Eq('portal_type', 'OpenProject') | Eq('portal_type', 'Document') | Eq('portal_type', 'OpenMember')) & Eq('SearchableText', search_query),
            rs,
            )
        return brains
    

class NewsView(SearchView):
    def news_items(self):
        news_path = '/'.join(self.context.portal.getPhysicalPath()) + '/news'
        query = dict(portal_type='Document',
                     sort_on='created',
                     sort_order='descending',
                     sort_limit=20,
                     path=news_path
                     )
        brains = self.catalogtool(**query)
        return brains
        
    def can_add_news(self):
        return self.membertool.checkPermission('Manage Portal', self.context)

    def subpoena_free(self):
        delta = zopedatetime() - self.dob_datetime
        return int(delta)
