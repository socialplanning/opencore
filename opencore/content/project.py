import os.path
import Products.OpenPlans.content.project as project
from Products.Fate.meta.view import AddView as BaseAddView
from opencore import redirect
try:
    from Products.OpenPlans.browser.projectlisting import ProjectListingView
except ImportError:
    from opencore.siteui.projectlisting import ProjectListingView
from memojito import memoizedproperty
from Products.CMFCore.utils import getToolByName
from Products.Five.traversable import Traversable
from zope.interface import implements
from opencore.interfaces import IAddSubProject

OpenProject=project.OpenProject
HOME_PAGE_ID = 'project-home'
HOME_PAGE_TITLE = 'Project Home'
HOME_PAGE_FILE = 'project_index.html'


class ProjectAddView(BaseAddView):
    """
    Perform initialization after creation.
    """
    def handle_environ(self):
        pass
        
    def createAndAdd(self):
        """
        Perform some post-creation initialization.
        """
        name = self.context.invokeFactory(self._portal_type,
                                          self._content_name)
        if name is None:
            name = self._content_name
        instance = self.context._getOb(name)
        # add the 'project home' menu item before any others
        instance._initProjectHomeMenuItem()
        # Fetch the values from request and store them.
        instance.processForm()
        # We don't need this here
        instance._initializeProject(self.request)

        # ugh... roster might have been created by an event before a
        # team was associated (in _initializeProject), need to fix up
        roster_id = instance.objectIds(spec='OpenRoster')
        if roster_id:
            roster = instance._getOb(roster_id[0])
            if not roster.getTeams():
                roster.setTeams(instance.getTeams())

        instance = self.handle_environ(instance)

        return instance

    
class SubProjectAddView(ProjectAddView):
    """add view for redirected areas
    """
    def __init__(self, view, request):
        self.context = view.context
        self.request = request
        self.context_view = view
        
    def handle_environ(self, instance):
        theme_parent = self.request.environ.get(redirect.PARENT_KEY, False)
        if theme_parent:
            parent = self.unrestrictedTraverse(theme_parent)
            redirect.handle_child_created(instance, parent)


class SubProjectListingView(ProjectListingView, Traversable): 
    """mandatory docstring
    """
    implements(IAddSubProject)

    @memoizedproperty
    def redirect_info(self): 
        return redirect.get_info(self.context)

    @property
    def project_paths(self):
        return list(self.redirect_info.values())

    @memoizedproperty
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')
        
    def allprojects(self): 
        return self.portal_catalog(path=self.project_paths, sort_on='sortable_title')
