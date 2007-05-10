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

Traversing to the url should yield the same class
   >>> view = self.portal.unrestrictedTraverse('projects/@@index.html')
   >>> view
   <Products.Five.metaclass.SimpleViewClass from ...>
