from Products.CMFCore.utils import getToolByName
from Products.Five.traversable import Traversable
from opencore import redirect
from opencore.interfaces.adding import IAddSubProject
from opencore.project.browser.projectlisting import ProjectListingView
from plone.memoize.instance import memoize, memoizedproperty
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

    def allprojects(self):
        pc = getToolByName(self.context, 'portal_catalog')
        return pc(portal_type='OpenProject',
                  path=self.project_paths,
                  sort_on='sortable_title')
    @memoize
    def blocked_content(self):
        name = self.__name__
        parent = self.aq_parent
        if name in parent.objectIds():
            return getattr(parent, name)
        return False
