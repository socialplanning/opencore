from Products.CMFPlone import Batch
from Products.AdvancedQuery import Eq, RankByQueries_Sum
from opencore.nui.opencoreview import OpencoreView

class PeopleSearchView(OpencoreView):

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
            self.search_results = self._get_batch(self.search_for_person_by_letter(letter_search, sort_by), start)
            self.search_query = 'for persons starting with &ldquo;%s&rdquo;' % letter_search
        elif projname:
            self.search_results = self._get_batch(self.search_for_person(projname, sort_by), start)
            self.search_query = 'for &ldquo;%s&rdquo;' % projname
            
        return self.index()

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

    def search_for_person_by_letter(self, letter, sort_by=None):
        letter = letter.lower()
        query = dict(portal_type="OpenMember",
                     Title=letter + '*')
        people_brains = self.catalogtool(**query)

        def matches(brain):
            title = brain.Title.lower()
            return title.startswith(letter) \
                or title.startswith('the ' + letter) \
                or title.startswith('a ' + letter) \
                or title.startswith('an ' + letter)

        people_brains = filter(matches, people_brains)

        def sort_key_fn(x):
            if sort_by is None: return 0

            prop = getattr(x, sort_by)
            if prop == 'relevancy': return 0
            
            if callable(prop):
                return prop()
            return prop

        people_brains.sort(key=sort_key_fn)

        return people_brains

    def search_for_person(self, person, sort_by=None):
        person = person.lower()

        proj_query = person
        if not proj_query.endswith('*'):
            proj_query = proj_query + '*'

        if not sort_by or sort_by == 'relevancy':
            rs = (RankByQueries_Sum((Eq('Title', proj_query),32), (Eq('getFull_name', proj_query),16)),)
        else:
            # we can't sort by title
            if sort_by == 'Title':
                sort_by = 'sortable_title'
            rs = ((sort_by, 'desc'),)

        people_brains = self.catalogtool.evalAdvancedQuery(
            Eq('portal_type', 'OpenMember') & Eq('SearchableText', proj_query),
            rs,
            )
        return people_brains
