import os.path
import cgi

from Acquisition import aq_parent

from zope import event
from zope.interface import implements, Interface
from zope.component import adapts

from Products.Five.traversable import Traversable
from Products.CMFCore.utils import getToolByName
from Products.Fate.meta.view import AddView as BaseAddView
#import Products.OpenPlans.content.project as project

from memojito import memoizedproperty, memoize

from projectlisting import ProjectListingView
from opencore import redirect
from opencore.interfaces.adding import IAddSubProject, IAddProject 
from opencore.interfaces import IProject
from opencore.interfaces.event import AfterProjectAddedEvent, AfterSubProjectAddedEvent
from zope.app.traversing.interfaces import ITraversable
from Products.Five.traversable import FiveTraversable

HOME_PAGE_ID = 'project-home'
HOME_PAGE_TITLE = 'Project Home'
HOME_PAGE_FILE = 'project_index.html'


# == project add views == #

class ProjectAddView(BaseAddView):
    """
    Perform initialization after creation.
    """
    def __init__(self, context, request):
        """
        Hide the tabs.
        """
        self.context = context
        self.request = request
        request.set('disable_border', 1)

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
        self.request.set('__initialize_project__', True)
        instance = self.instance()
        event.notify(AfterProjectAddedEvent(instance, self.request))
        return instance

    def redirect(self):
        """
        Redirect to login page if not logged in.
        """
        mtool = getToolByName(self.context, 'portal_membership')
        final_url = "%s/do_add_project" % self.context.absolute_url()
        if mtool.isAnonymousUser():
            final_url = cgi.urllib.quote(final_url)
            portal_url = getToolByName(self.context, 'portal_url')()
            redirect = "%s/login_form?came_from=%s" % (portal_url,
                                                       final_url)
            self.request.response.redirect(redirect)
        else:
            self.request.response.redirect(final_url)

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
    @memoize
    def blocked_content(self):
        name = self.__name__
        parent = self.aq_parent
        if name in parent.objectIds():
            return getattr(parent, name)
        return False


