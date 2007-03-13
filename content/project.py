import os.path
import Products.OpenPlans.content.project as project
from Products.Fate.meta.view import AddView as BaseAddView
from opencore import redirect
try:
    from Products.OpenPlans.browser.projectlisting import ProjectListingView
except ImportError:
    from opencore.siteui.projectlisting import ProjectListingView
from memojito import memoizedproperty, memoize
from Products.CMFCore.utils import getToolByName
from Products.Five.traversable import Traversable
from zope.interface import implements
from zope.component import adapter, adapts
from opencore.interfaces import IAddSubProject, IAddProject, IProject
from opencore.interfaces.event import AfterProjectAddedEvent, \
     AfterSubProjectAddedEvent
from opencore.interfaces.event import IAfterProjectAddedEvent, \
     IAfterSubProjectAddedEvent
from zope import event
from Acquisition import aq_parent

OpenProject=project.OpenProject
HOME_PAGE_ID = 'project-home'
HOME_PAGE_TITLE = 'Project Home'
HOME_PAGE_FILE = 'project_index.html'


# == project add views == #

class ProjectAddView(BaseAddView):
    """
    Perform initialization after creation.
    """
    @memoize
    def projects_container(self):
        """climb acquisition and find the proper container for project
        adding"""
        obj = self
        while obj is not None and not IAddProject.providedBy(obj):
            obj = aq_parent(obj)
        return obj

    @memoize
    def instance(self):
        projects = self.projects_container() 
        name = projects.invokeFactory(self._portal_type, self._content_name)
        if name is None:
            name = self._content_name
        return projects._getOb(name)

    def createAndAdd(self):
        """
        Perform some post-creation initialization.
        """
        instance = self.instance()
        event.notify(AfterProjectAddedEvent(instance, self.request))
        return instance
    
    
class SubProjectAddView(ProjectAddView):
    """add view for creating projects as subprojects of themed areas
    """
    
    def __init__(self, view, request):
        self.context = view.context
        self.request = request
        self.context_view = view

    def createAndAdd(self):
        instance = self.instance()
        event.notify(AfterSubProjectAddedEvent(instance, self.context, 
                                               self.request))
        return instance 

# ==  post creation handlers == #

@adapter(IAfterProjectAddedEvent)
def handle_postcreation(event):
    instance = event.project

    # add the 'project home' menu item before any others
    instance._initProjectHomeMenuItem()

    # Fetch the values from request and store them.
    instance.processForm()

    # We don't need this here
    instance._initializeProject(event.request)

    # ugh... roster might have been created by an event before a
    # team was associated (in _initializeProject), need to fix up
    roster_id = instance.objectIds(spec='OpenRoster')
    if roster_id:
        roster = instance._getOb(roster_id[0])
        if not roster.getTeams():
            roster.setTeams(instance.getTeams())


@adapter(IAfterSubProjectAddedEvent)
def handle_subproject_redirection(event):
    instance = event.project
    request = event.request
    parent = event.parent 
    _handle_parent_child_association(parent, instance)


def _handle_parent_child_association(parent, child):
    child_id = child.getId()
    parent_info = redirect.get_info(parent)
    parent_path = redirect.pathstr(child)
    parent_info[child_id] = parent_path
    child_url = "%s/%s" %(parent_info.url, child_id) 
    redirect.activate(child, url=child_url, parent=parent_path)


# == other views == #


class SubProjectListingView(ProjectListingView, Traversable): 
    """mandatory docstring
    """
    implements(IAddSubProject)

    def __init__(self, context, request): 
        ProjectListingView.__init__(self, context, request)
        # XXX this may be a horrendous hack, but it appears 
        # to be what Five expects to find during traversal... ?!
        self.REQUEST = request 
    
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
        return self.portal_catalog(portal_type='OpenProject',
                                   path=self.project_paths,
                                   sort_on='sortable_title')

# default redirection 

class DefaultProjectRedirectTraverser(redirect.DefaultingRedirectTraverser): 
    """
    a traverser that redirects non-IRedirected IProjects to a 
    default host / path
    """
    adapts(IProject)
