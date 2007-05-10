# projects page classes
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFPlone import Batch
from Products.AdvancedQuery import Eq, RankByQueries_Sum
 
from opencore.nui.opencoreview import OpencoreView

class ProjectsView(OpencoreView):

    template = ZopeTwoPageTemplateFile('projects.pt')

    def recentprojects(self):
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
            
        return self.template()
            
    def _get_batch(self, brains, start=0):
        return Batch(brains,
                     size=3,
                     start=start,
                     end=0,
                     orphan=0,
                     overlap=0,
                     pagerange=6,
                     quantumleap=0,
                     b_start_str='b_start')

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

        def sort_key_fn(x):
            if sort_by is None: return 0

            prop = getattr(x, sort_by)
            if prop == 'relevancy': return 0
            
            if callable(prop):
                return prop()
            return prop

        project_brains.sort(key=sort_key_fn)

        return project_brains

    def search_for_project(self, project, sort_by=None):
        project = project.lower()

        proj_query = project
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
    
    def create_date(self, project):
        cd = project.CreationDate()
        time_obj = strptime(cd, '%Y-%m-%d %H:%M:%S')
        datetime_obj = datetime.datetime(*time_obj[0:6])
        return prettyDate(datetime_obj)


class ProjectsResultsView(ProjectsView):
    template = ZopeTwoPageTemplateFile('projects-searchresults.pt')
    
class PeopleResultsView(ProjectsView):
    template = ZopeTwoPageTemplateFile('people-searchresults.pt')

class HomeView(ProjectsView):
    template = ZopeTwoPageTemplateFile('home.pt')

class PeopleView(ProjectsView):
    template = ZopeTwoPageTemplateFile('people.pt')
