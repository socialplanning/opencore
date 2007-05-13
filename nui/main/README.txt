====================
views for main pages
====================

Instantiate a new projects view
   >>> from opencore.nui.main import search
   >>> request = self.portal.REQUEST
   >>> view = search.SearchView(self.portal.projects, request)

Get the list of projects that were recently updated
   >>> recent_projects = view.recentprojects()
   >>> recent_titles = [p.Title() for p in recent_projects]
   >>> recent_titles.sort()
   >>> recent_titles
   ['Proj1', 'Proj2', 'Proj3', 'Proj4']

Test searching for projects that start with a letter
   >>> brains = view.search_for_project_by_letter('P')
   >>> titles = [p.Title for p in brains]
   >>> titles
   ['Proj4', 'Proj1', 'Proj3', 'Proj2']

Now try sorting the projects
   >>> brains = view.search_for_project_by_letter('P', sort_by='modified')
   >>> [b.Title for b in brains]
   ['Proj2', 'Proj3', 'Proj1', 'Proj4']

Explicitly sort on relevancy
   >>> brains = view.search_for_project_by_letter('P', sort_by='relevancy')
   >>> titles = [p.Title for p in brains]
   >>> titles
   ['Proj4', 'Proj1', 'Proj3', 'Proj2']


Searching for a letter that doesn't match any projects
   >>> view.search_for_project_by_letter('X')
   []

Search for a project by string
   >>> brains = view.search_for_project('Proj3')
   >>> len(brains)
   1
   >>> brains[0].Title
   'Proj3'

Try a substring search
   >>> brains = view.search_for_project('Proj')
   >>> titles = [b.Title for b in brains]
   >>> titles.sort()
   >>> titles
   ['Proj1', 'Proj2', 'Proj3', 'Proj4']

And now sort them by creation time
   >>> brains = view.search_for_project('Proj', sort_by='created')
   >>> [b.Title for b in brains]
   ['Proj2', 'Proj3', 'Proj1', 'Proj4']

Traversing to the url should yield the same class
   >>> view = self.portal.projects.unrestrictedTraverse('@@index.html')
   >>> view
   <Products.Five.metaclass.SimpleViewClass from ...projects.pt object at...>

Render the view to see if there are any errors
   >>> response = view()

Get a view to the people page
Instantiate a new projects view
   >>> from opencore.nui.main import people
   >>> request = self.portal.REQUEST
   >>> view = people.PeopleSearchView(self.portal.people, request)

Get the list of people matching the search
   >>> people = view.search_for_person('test_user_1_')
   >>> people[0].getId
   'test_user_1_'
   >>> len(people)
   1

Search for people starting with a letter
   >>> people = view.search_for_person_by_letter('M')
   >>> names = [p.getId for p in people]
   >>> names
   ['m2', 'm3', 'm1', 'm4']

Search for members starting with a letter, only sort the results
   >>> people = view.search_for_person_by_letter('M', sort_by='getId')
   >>> names = [p.getId for p in people]
   >>> names
   ['m1', 'm2', 'm3', 'm4']

Search, explicitly specifying relevancy sort
   >>> people = view.search_for_person_by_letter('M', sort_by='relevancy')
   >>> names = [p.getId for p in people]
   >>> names
   ['m2', 'm3', 'm1', 'm4']

Traversing to the correct people search url should yield the same class
XXX currently is a name, because we don't have a special interface for
the people folder
   >>> view = self.portal.people.unrestrictedTraverse('peoplesearch')
   >>> view
   <Products.Five.metaclass.SimpleViewClass from ...people.pt object at...>

Render the view to see if there are any errors
   >>> response = view()
