import datetime
from DateTime import DateTime as zopedatetime
from time import strptime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import Batch
from Products.AdvancedQuery import Eq, RankByQueries_Sum
from topp.utils.pretty_date import prettyDate
from zExceptions import Redirect 
from opencore.nui.base import BaseView


class SearchView(BaseView):

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

    def pretty_date(self, date):
        try:
            time_obj = strptime(date, '%Y-%m-%d %H:%M:%S')
            datetime_obj = datetime.datetime(*time_obj[0:6])
        except TypeError:
            datetime_obj = date
        return prettyDate(datetime_obj)


def first_letter_match(title, letter):
    return title.startswith(letter) \
           or title.startswith('the ' + letter) \
           or title.startswith('a ' + letter) \
           or title.startswith('an ' + letter)

class ProjectsSearchView(SearchView):
    match = staticmethod(first_letter_match)

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

        if sort_by != 'relevancy':
            query['sort_on'] = sort_by

        project_brains = self.catalog(**query)

        project_brains = [brain for brain in project_brains \
                          if self.match(brain.Title.lower(), letter)]

        return project_brains

    def search_for_project(self, project, sort_by=None):
        proj_query = project.lower().strip()

        if proj_query == '*':
            return []
        if not proj_query.endswith('*'):
            proj_query = proj_query + '*'

        if not sort_by or sort_by == 'relevancy':
            rs = RankByQueries_Sum((Eq('Title', proj_query),32),
                                   (Eq('getFull_name', proj_query),16)),
        else:
            # we can't sort by title
            if sort_by == 'Title':
                sort_by = 'sortable_title'
            rs = ((sort_by, 'desc'),)

        project_brains = self.catalog.evalAdvancedQuery(
            Eq('portal_type', 'OpenProject') & Eq('SearchableText', proj_query),
            rs,
            )
        return project_brains
    
    def recently_updated_projects(self):
        query = dict(portal_type='OpenProject',
                     sort_on='modified',
                     sort_order='descending',
                     sort_limit=5,
                     )

        project_brains = self.catalog(**query) 
        # XXX expensive $$$
        # we get object for number of project members
        projects = (x.getObject() for x in project_brains)
        return projects


class PeopleSearchView(SearchView):
    def __init__(self, context, request):
        SearchView.__init__(self, context, request)

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
        user_query = letter + '*'
        query = dict(RosterSearchableText=user_query)
        if sort_by != 'relevancy':
            query['sort_on'] = sort_by

        people_brains = self.membranetool(**query)
        people_brains = [brain for brain in people_brains if brain.getId.lower().startswith(letter)]
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
            rs = ((sort_by, 'desc'),)

        people_brains = self.membranetool.evalAdvancedQuery(
            Eq('RosterSearchableText', person_query),
            rs,
            )
        return people_brains

    def no_home(self, userid):
        """ check to see if a user has a people folder (has logged in)
            note: not using mtool.getHomeFolder for efficiency reasons """
        return not self.context.has_key(userid)

    def add_class_to_img(self, imgdata, clss):
        tag = str(imgdata)
        return tag.replace('<img', '<img class="%s"' % clss)


class HomeView(SearchView):
    """zpublisher"""
    def __init__(self, context, request):
        # redirect asap
        go_here = request.get('go_here', None)
        if go_here:
            raise Redirect, go_here        
        SearchView.__init__(self, context, request)

        self.projects_search = ProjectsSearchView(context, request)
        
    def intro(self):
        return self.render_static('main_home_intro.txt')

    def recently_updated_projects(self):
        return self.projects_search.recently_updated_projects()

    def recently_created_projects(self):
        query = dict(portal_type='OpenProject',
                     sort_on='Creator',
                     sort_order='descending',
                     sort_limit=5,
                     )

        project_brains = self.catalog(**query) 
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
        brains = self.catalog(**query)
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
            if sort_by == 'getId':
                rs = ((sort_by, 'asc'),)
            else:
                rs = ((sort_by, 'desc'),)

        brains = self.catalog.evalAdvancedQuery(
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
        brains = self.catalog(**query)
        return brains
        
    def can_add_news(self):
        return self.membertool.checkPermission('Manage Portal', self.context)

    def subpoena_free(self):
        delta = zopedatetime() - self.dob_datetime
        return int(delta)
