import re

from DateTime import DateTime as zopedatetime
from zExceptions import Redirect 

from zope.interface import alsoProvides

from Products.AdvancedQuery import Eq, RankByQueries_Sum
from Products.CMFPlone.PloneBatch import Batch

from opencore import redirect
from opencore.interfaces import INewsItem
from opencore.browser.base import BaseView

num_regex = re.compile('((the|a|an)\s+)?[0-9]+')

def first_letter_match(title, letter):
    if letter == 'num':
        return num_regex.match(title)
    else:
        return title.startswith(letter) \
               or title.startswith('the ' + letter) \
               or title.startswith('a ' + letter) \
               or title.startswith('an ' + letter)

def clean_search_query(search_query):
    search_query = search_query.lower().strip()    
    
    bad_chars = ["(", ")"]
    for char in bad_chars:
        search_query = search_query.replace(char, '"%s"' % char)
    return search_query


def _sort_by_id(brains):
    """
    This is a function, not a method, so it can be called from
    assorted view classes.
    """
    return sorted(brains, key=lambda x: x.getId.lower() or x.Title.lower())

def _sort_by_modified(brains):
    return sorted(brains, key=lambda x: x.modified)

def _sort_by_created(brains):
    return sorted(brains, key=lambda x:x.created, reverse=True)

def _sort_by_portal_type(brains):
    return sorted(brains, key=lambda b: (b.portal_type, b.id))

def searchForPerson(mcat, search_for, sort_by=None):
    """
    This is a function, not a method, so it can be called from
    assorted view classes.
    """
    person_query = clean_search_query(search_for)

    if person_query == '*':
        return []

    if not person_query.endswith('*'):
        person_query = person_query + '*'

    if not sort_by or sort_by == 'relevancy':
        rs = (RankByQueries_Sum((Eq('Title', person_query),32),
                                (Eq('getId', person_query),16)),)
    else:
        rs = ((sort_by, 'asc'),)

    people_brains = mcat.evalAdvancedQuery(
        Eq('RosterSearchableText', person_query),
        rs,
        )

    if sort_by == 'getId':
        people_brains = _sort_by_id(people_brains)
    return people_brains
    
import lxml.html
class SearchView(BaseView):

    def batched_results(self):
        results = self.handle_request()
        
        batch_size = self.batch_size
        start = self.from_page(self.page, batch_size)
        return self._get_batch(results, start, batch_size)

    def handle_request(self):
        """
        A default search handler that finds all content
        published underneath the current context while
        respecting security.  The `sort_by` key from the
        request is passed through to the catalog tool,
        so unexpected sort keys may throw an error.

        Override this method in a subclass to customize 
        searching or sorting behavior.
        """

        cat = self.get_tool('portal_catalog')
        path = '/'.join(self.context.getPhysicalPath())
        results = cat(path=path, sort_on=self.sort_by)

        return results        

    def sort_widget_string(self, batch):
        """
        return an HTML snippet like "Projects 1-12 of 34"
        should be i18nified, with two distinct strings for single
        and plural, i think.
        """
        is_plural = False
        if batch.end > batch.start: is_plural = True
        html = self._sortable_fields(start=batch.start,
                                     end=batch.end,
                                     sequence_length=batch.sequence_length,
                                     is_plural=is_plural)
        html = lxml.html.fromstring(html)
        div = html.get_element_by_id('sort_string')
        assert div.tag.lower() == 'div'

        return div.text

    @property
    def sort_by_options(self):
        html = self._sortable_fields(start='foo',
                                     end='bar',
                                     sequence_length='morx',
                                     is_plural='fleem')

        html = lxml.html.fromstring(html)
        ul = html.get_element_by_id('sortable_fields')
        assert ul.tag.lower() == 'ul'

        _sort_by_options = dict()
        for li in ul:
            key = li.get('id')
            _sort_by_options[key] = li.text
        return _sort_by_options

    @property
    def search_for(self):
        return self.request.get('search_for', None)

    @property
    def letter_search(self):
        return self.request.get('letter_search', None)

    @property
    def sort_by(self):
        return self.request.get('sort_by', None)

    @property
    def batch_size(self):
        try:
            return int(self.request.get('batch_size', 10))
        except ValueError:
            return 10

    @property
    def page(self):
        try:
            return int(self.request.form.get('page', 1))
        except ValueError:
            return 1
        

    def _get_batch(self, brains, start=0, size=10):
        return Batch(brains,
                     size=size,
                     start=start,
                     end=0,
                     orphan=0,
                     overlap=0,
                     pagerange=6,
                     quantumleap=0,
                     b_start_str='b_start')

    def from_page(self, page, batch_size):
        return batch_size * (page - 1)
    
    noun = 'please define a plural noun in your subclass'

    def search_by_letter(self, letter, sort_by):
        """
        search for content by its initial letter.
        a subclass needs to define this method
        """
        pass

    def search_by_text(self, search_for, sort_by):
        """
        search for content by text query.
        a subclass needs to define this method
        """


from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
class ProjectsSearchView(SearchView):

    noun = 'projects'
    active_states = ['public', 'private']

    _sortable_fields = ZopeTwoPageTemplateFile('projects-sortwidget.pt')
    
    def handle_request(self):
        self.search_results = None
        self.search_query = None

        if self.letter_search:
            search_results = self.search_by_letter(self.letter_search, self.sort_by)
        elif self.search_for:
            search_results = self.search_by_text(self.search_for, self.sort_by)
        else:
            search_results = self.search_by_letter('all', self.sort_by)

        return search_results


    def logo_for_proj_brain(self, brain):
        ## XXX TODO: i'm sure we have a more efficient way of doing this now!
        proj = brain.getObject()
        return proj.getLogo()

    def search_by_letter(self, letter, sort_by=None):
        letter = letter.lower()

        if letter == 'num':
            search_for = '1* OR 2* OR 3* OR 4* OR 5* OR 6* OR 7* OR 8* OR 9* OR 0*'
            query = dict(portal_type="OpenProject", Title=search_for)
        elif letter == 'all':
            query = dict(portal_type="OpenProject")
        else:
            search_for = letter + '*'
            query = dict(portal_type="OpenProject", Title=search_for)

        if sort_by is None:
            sort_by = 'sortable_title'
        query['sort_on'] = sort_by

        project_brains = self.catalog(**query)

        if letter == 'all':
            return project_brains

        project_brains = [brain for brain in project_brains \
                          if first_letter_match(brain.Title.lower(), letter)]

        return project_brains

    def search_by_text(self, search_for, sort_by=None):
        project = search_for
        proj_query = clean_search_query(project)

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

        query = Eq('portal_type', 'OpenProject') & Eq('SearchableText', proj_query)

        project_brains = self.catalog.evalAdvancedQuery(query, rs)
        return project_brains
    
    def recently_updated_projects(self, sort_limit=10):
        
        rs = (('modified', 'desc'),)
            
        query = Eq('portal_type', 'OpenProject') & (Eq('project_policy', 'open_policy') | Eq('project_policy', 'medium_policy'))

        project_brains = self.catalog.evalAdvancedQuery(query, rs)
        return project_brains[:sort_limit]

    # what is an n_project_member?
    def n_project_members(self, proj_brain):
        proj_id = proj_brain.getId
        tmtool = self.get_tool('portal_teams')
        team_path = '/'.join(tmtool.getPhysicalPath())
        team_path = '%s/%s' % (team_path, proj_id)
        brains = self.catalog(portal_type='OpenMembership',
                              path=team_path,
                              review_state=self.active_states,
                              )
        return len(brains)


class PeopleSearchView(SearchView):

    noun = 'members'

    _sortable_fields = ZopeTwoPageTemplateFile('people-sortwidget.pt')

    def handle_request(self):
        self.search_results = None
        self.search_query = None

        if self.letter_search:
            search_results = self.search_by_letter(self.letter_search, self.sort_by)
        elif self.search_for:
            search_results = self.search_by_text(self.search_for, self.sort_by)
        else:
            search_results = self.search_by_letter('all', self.sort_by)

        return search_results

    def search_by_letter(self, letter, sort_by=None):
        letter = letter.lower()

        if letter == 'num':
            search_for = '1* OR 2* OR 3* OR 4* OR 5* OR 6* OR 7* OR 8* OR 9* OR 0*'
            query = dict(RosterSearchableText=search_for)
        elif letter == 'all':
            query = {}
        else:
            search_for = letter + '*'
            query = dict(RosterSearchableText=search_for)

        query['sort_on'] = sort_by

        people_brains = self.membranetool(**query)

        if letter == 'all':
            return people_brains
        elif letter == 'num':
            people_brains = [brain for brain in people_brains
                             if num_regex.match(brain.getId.lower())]
        else:
            people_brains = [brain for brain in people_brains
                             if brain.getId.lower().startswith(letter)]

        if not sort_by or sort_by == 'getId':
            people_brains = _sort_by_id(people_brains)

        return people_brains

    def search_by_text(self, search_for, sort_by=None):
        return searchForPerson(self.membranetool, search_for, sort_by)

    def recently_created_members(self, sort_limit=5):
        query = dict(sort_on='created',
                     sort_order='descending',
                     sort_limit=sort_limit)
        brains = self.membranetool(**query)
        
        return _sort_by_created(brains)



class SitewideSearchView(SearchView):

    noun = 'content'

    _sortable_fields = ZopeTwoPageTemplateFile('home-sortwidget.pt')

    def handle_request(self):
        self.search_results = None
        self.search_query = None

        if self.letter_search:
            search_results = self.search_by_letter(self.letter_search, self.sort_by)
        elif self.search_for:
            search_results = self.search_by_text(self.search_for, self.sort_by)
        else:
            search_results = self.search_by_letter('all', self.sort_by)

        return search_results

    def search_by_letter(self, letter, sort_by=None):
        letter = letter.lower()
        if letter == 'num':
            search_for = '1* OR 2* OR 3* OR 4* OR 5* OR 6* OR 7* OR 8* OR 9* OR 0*'
            catalog_query = (Eq('portal_type', 'OpenProject') & Eq('Title', search_for)) \
                    | (Eq('portal_type', 'Document') & Eq('Title', search_for))
            membrane_query = dict(portal_type="OpenMember",
                                  RosterSearchableText=search_for)
        elif letter == 'all':
            catalog_query = Eq('portal_type', 'OpenProject') \
                    | Eq('portal_type', 'Document')
            membrane_query = dict(portal_type="OpenMember")
        else:
            search_for = letter + '*'
            catalog_query = ((Eq('portal_type', 'OpenProject') & (Eq('Title', search_for))) \
                    | (Eq('portal_type', 'Document') & (Eq('Title', search_for))))
            membrane_query = dict(portal_type="OpenMember",
                                  RosterSearchableText=search_for)


        if not sort_by:
            sort_by = 'getId'

        brains = self.catalog.evalAdvancedQuery(catalog_query, ()) + \
                 self.get_tool('membrane_tool')(membrane_query)

        if sort_by == 'getId':
            brains = _sort_by_id(brains)
        elif sort_by == 'modified':
            brains = _sort_by_modified(brains)
        elif sort_by == 'portal_type':
            brains = _sort_by_portal_type(brains)

        if letter == 'all':
            return brains
        
        out_brains = []
        
        for brain in brains:
            if brain.portal_type in ('OpenProject', 'Document') and \
                   first_letter_match(brain.Title.lower(), letter):
                out_brains.append(brain)
            elif brain.portal_type == ('OpenMember') and \
                    brain.getId.lower().startswith(letter):
                out_brains.append(brain)
                
        return out_brains

    def search_by_text(self, search_for, sort_by=None):
        search_query = clean_search_query(search_for)
    
        if search_query == '*':
            return []

        if not search_query.endswith('*'):
            search_query = search_query + '*'

        if not sort_by or sort_by == 'relevancy':
            rs = (RankByQueries_Sum((Eq('getId', search_query),32), (Eq('getFull_name', search_query),16)),)
        else:
            if sort_by == 'getId':
                rs = ()
            else:
                rs = ((sort_by, 'desc'),)

        query = (Eq('portal_type', 'OpenProject') \
                | Eq('portal_type', 'Document') \
                | Eq('portal_type', 'OpenMember')) \
                & Eq('SearchableText', search_query)
        brains = self.catalog.evalAdvancedQuery(query, rs)

        if sort_by == 'getId':
            brains = _sort_by_id(brains)

        return brains


class HomeView(SearchView):
    """zpublisher"""

    def __init__(self, context, request):
        # redirect asap
        go_here = request.get('go_here', None)
        if go_here:
            raise Redirect, go_here        
        SearchView.__init__(self, context, request)

        # don't do this!
        self.projects_search = ProjectsSearchView(context, request)


    def recently_updated_projects(self):
        created_brains = self.recently_created_projects()
        updated_brains = self.projects_search.recently_updated_projects(sort_limit=10)
        out = []
        count = 0
        for ubrain in updated_brains:
            not_redundant = 1
            for cbrain in created_brains:
                if ubrain.getId == cbrain.getId:
                    not_redundant = 0
                    
            if not_redundant == 1:
                out.append(ubrain)
                count+=1
            if count == 5:
                return out
            
        return out

    def recently_created_members(self):
        query = dict(sort_on='created',
                     sort_order='descending',
                     sort_limit=5)
        brains = self.membranetool(**query)
        
        return _sort_by_created(brains)

    def n_project_members(self, proj_brain):
        return self.projects_search.n_project_members(proj_brain)

    def recently_created_projects(self):
        rs = (('created', 'desc'),)
            
        query = Eq('portal_type', 'OpenProject') & (Eq('project_policy', 'open_policy') | Eq('project_policy', 'medium_policy'))
        
        project_brains = self.catalog.evalAdvancedQuery(query, rs)
        return project_brains[:5]


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
        delta = zopedatetime() - self.portal.created()
        return int(delta)

    def _get_new_id(self):
        # if you don't like this
        # return zopedatetime().millis()
        # this is informative
        return zopedatetime().strftime('%Y%m%d%H%M%S')

    def add_new_news_item(self):
        new_id = self._get_new_id()
        self.context.invokeFactory('Document', id=new_id, title=new_id)
        item = getattr(self.context, new_id)
        alsoProvides(item, INewsItem)
        edit_url = '%s/edit' % item.absolute_url()
        self.request.response.redirect(edit_url)

