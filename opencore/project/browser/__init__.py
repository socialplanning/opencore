from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName
from Products.Five.traversable import Traversable
from memojito import memoizedproperty, memoize
from opencore import redirect
from opencore.interfaces.adding import IAddSubProject
from projectlisting import ProjectListingView
from zope.interface import implements


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
        parent = aq_parent(self)
        if name in parent.objectIds():
            return getattr(parent, name)
        return False
