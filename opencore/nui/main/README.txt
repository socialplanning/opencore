====================
views for main pages
====================

Projects
========

Instantiate a new projects view::

   >>> from opencore.nui.main import search
   >>> request = self.portal.REQUEST
   >>> view = search.ProjectsSearchView(self.portal.projects, request)

Acquistion wrap it::

   >>> view = view.__of__(self.portal.projects)

Test for aq issues::

   >>> view.portal
   <PloneSite at /plone>

Get the list of projects that were recently updated::

   >>> recent_projects = view.recently_updated_projects()
   >>> recent_titles = [p.Title for p in recent_projects]
   >>> recent_titles.sort()
   >>> recent_titles
   ['Project Four', 'Project One', 'Project Three', 'Project Two']

Test searching for projects that start with a letter::

   >>> brains = view.search_for_project_by_letter('X')
   >>> [p.Title for p in brains]
   []

   >>> brains = view.search_for_project_by_letter('P')
   >>> titles = [p.Title for p in brains]
   >>> titles.sort()
   >>> titles
   ['Project Four', 'Project One', 'Project Three', 'Project Two']


@@ sorting is a little unclear. is this accurate/correct behavior?
what is relevance, how is it effected? why is Proj2 the most recently modified?

Now try sorting the projects::

   >>> brains = view.search_for_project_by_letter('P', sort_by='modified')
   >>> [b.Title for b in brains]
   ['Project Two', 'Project Three', 'Project One', 'Project Four']

Explicitly sort on relevancy::

   >>> brains = view.search_for_project_by_letter('P', sort_by='relevancy')
   >>> titles = [p.Title for p in brains]
   >>> titles
   ['Project Four', 'Project One', 'Project Three', 'Project Two']


Searching for a letter that doesn't match any projects::

   >>> brains = view.search_for_project_by_letter('X')
   >>> titles = [p.Title for p in brains]
   >>> titles
   []

Searching for all projects::

   >>> brains = view.search_for_project_by_letter('all')
   >>> titles = [p.Title for p in brains]
   >>> titles
   ['Project Two', 'Project Three', 'Project One', 'Project Four']

Searching for projects starting with a number::

   >>> brains = view.search_for_project_by_letter('num')
   >>> titles = [p.Title for p in brains]
   >>> titles
   []

Create a project that starts with a number::
    >>> form_vars = dict(id='5test', __initialize_project__=True,
    ...                  title='5test',
    ...                  workflow_policy='medium_policy',
    ...                  add=True, featurelets = ['listen'], set_flets=1)
    >>> proj_view = self.portal.projects.restrictedTraverse("create")
    >>> proj_view.request.form.update(form_vars)
    >>> out = proj_view.handle_request()

Now search again::

   >>> brains = view.search_for_project_by_letter('num')
   >>> titles = [p.Title for p in brains]
   >>> titles
   ['5test']

Search for a project by string::

   >>> brains = view.search_for_project('Three')
   >>> len(brains)
   1
   >>> brains[0].Title
   'Project Three'

Try a substring search::

   >>> brains = view.search_for_project('Proj')
   >>> titles = [b.Title for b in brains]
   >>> titles.sort()
   >>> titles
   ['Project Four', 'Project One', 'Project Three', 'Project Two']

And now sort them by creation time::

@@ I'm getting some irregular failures here. dwm.

   >>> brains = view.search_for_project('Proj', sort_by='created')
   >>> [b.Title for b in brains]
   ['Project Four', 'Project One', 'Project Three', 'Project Two']

   old: ['Proj2', 'Proj3', 'Proj1', 'Proj4']

Traversing to the url should yield the same class::

   >>> view = self.portal.projects.unrestrictedTraverse('@@view')
   >>> view
   <Products.Five.metaclass.SimpleViewClass from ...projects.pt object at...>

Render the view to see if there are any errors::

   >>> response = view()

People Page
===========

Instantiate a new projects view::

   >>> request = self.portal.REQUEST
   >>> view = search.PeopleSearchView(self.portal.people, request)

Get the list of people matching the search::

   >>> people = view.search_for_person('m4')
   >>> people[0].getId
   'm4'
   >>> len(people)
   1

Search for people starting with a letter::

   >>> people = view.search_for_person_by_letter('M')
   >>> names = [p.getId for p in people]
   >>> names
   ['m2', 'm3', 'm1', 'm4']

Search for people starting with a number::

   >>> people = view.search_for_person_by_letter('num')
   >>> names = [p.getId for p in people]
   >>> names
   []

Search for all people::

   >>> people = view.search_for_person_by_letter('all')
   >>> names = [p.getId for p in people]

test_user_1 shows up here, and I don't know if anyone's entirely sure
whether that's a good or a bad thing, but let's let the test pass::
   >>> sorted(names)
   ['m1', 'm2', 'm3', 'm4', 'test_user_1_']

Search for members starting with a letter, only sort the results::

   >>> people = view.search_for_person_by_letter('M', sort_by='getId')
   >>> names = [p.getId for p in people]
   >>> names
   ['m1', 'm2', 'm3', 'm4']

Search, explicitly specifying relevancy sort::

   >>> people = view.search_for_person_by_letter('M', sort_by='relevancy')
   >>> names = [p.getId for p in people]
   >>> names
   ['m2', 'm3', 'm1', 'm4']

Search for members, explicitly specifying full name sort::

   >>> people = view.search_for_person_by_letter('M', sort_by='exact_getFullname')
   >>> names = [p.getFullname for p in people]
   >>> names
   ['Member Four', 'Member One', 'Member Three', 'Member Two']

Traversing to the correct people search url should yield the same class
XXX currently is a name, because we don't have a special interface for
the people folder::

   >>> view = self.portal.people.unrestrictedTraverse('@@view')
   >>> view
   <Products.Five.metaclass.SimpleViewClass from ...people.pt object at...>

Render the view to see if there are any errors::

   >>> response = view()

Navigating to the portal home should not produce any errors::

   >>> view = self.portal.unrestrictedTraverse('@@view')
   >>> view
   <Products.Five.metaclass.SimpleViewClass from ...home.pt object at...>

Render the view to see if there are any errors::

   >>> response = view()

Render the projects search results view with no search::

   >>> view = self.portal.projects.unrestrictedTraverse('searchresults')
   >>> response = view()

Render the people search results view with no search::

   >>> view = self.portal.people.unrestrictedTraverse('searchresults')
   >>> response = view()

Test the news view::

   >>> view = self.portal.news.unrestrictedTraverse('@@view')
   >>> view
   <Products.Five.metaclass.SimpleViewClass from ...news.pt object at...>

   >>> view.news_items()
   []

Check our static content::

   >>> view.sidebar()
   '...'

We shouldn't have an add link because we're not the admin
   >>> result = view()
   >>> 'Add news item...' in result
   False

When we login as admin, we should have the link
   >>> self.logout()
   >>> self.loginAsPortalOwner()
   >>> view.loggedinmember.getId = lambda *a:'whatever'
   >>> result = view()
   >>> 'Add news item...' in result
   True

Now that we have permission to add a new news item, let's do so
   >>> view.add_new_news_item()
   >>> view.request.response.getHeader('location')
   'http://nohost/plone/news/.../edit'

And we have a news item now
   >>> len(view.news_items())
   1


Sitewide Search
===============

   >>> view = search.SitewideSearchView(self.portal.projects, request)
   >>> brains = view.search('Proj')
   >>> len(brains)
   9
   >>> brains = view.search_by_letter('p')
   >>> len(brains)
   9
   >>> brains = view.search_by_letter('m', sort_by='getId')
   >>> [b.getId for b in brains]
   ['m1', 'm2', 'm3', 'm4']

Search for everything::
   >>> brains = view.search_by_letter('all', sort_by='getId')
   >>> len(brains)
   18

Search for things starting with a number::
   >>> brains = view.search_by_letter('num')
   >>> ids = [b.getId for b in brains]
   >>> len(ids)
   2
   >>> '5test' in ids
   True


Homepage View
=============

   >>> view = search.HomeView(self.portal, request)
   >>> brains = view.recently_created_projects()
   >>> [b.getId for b in brains]
   ['5test', 'p4', 'p1', 'p3', 'p2']
   >>> for i in range(len(brains)-1):
   ...
   ...     brains[i].CreationDate >= brains[i+1].CreationDate
   True
   True
   True
   True

Check that the project url method works
   >>> brain = brains[-1]
   >>> view.project_url(brain)
   'http://nohost/plone/projects/p2'
   >>> view.n_project_members(brain)
   4
