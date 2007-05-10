====================
views for main pages
====================

Instantiate a new projects view
   >>> from opencore.nui.main import projects
   >>> request = self.portal.REQUEST
   >>> view = projects.ProjectsView(self.portal.projects, request)

Get the list of projects that were recently updated
   >>> recent_projects = view.recentprojects()
   >>> recent_titles = [p.Title() for p in recent_projects]
   >>> recent_titles.sort()
   >>> recent_titles
   ['Proj1', 'Proj2', 'Proj3', 'Proj4']

Test searching for projects that start with a letter
   >>> brains = view.search_for_project_by_letter('P')
   >>> titles = [p.Title for p in brains]
   >>> titles.sort()
   >>> titles
   ['Proj1', 'Proj2', 'Proj3', 'Proj4']

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

Traversing to the url should yield the same class
   >>> view = self.portal.projects.unrestrictedTraverse('oc-projects')
   >>> view
   <Products.Five.metaclass.SimpleViewClass from ...projects.pt object at...>

Render the view to see if there are any errors
   >>> response = view()
