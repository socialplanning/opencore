from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.AdvancedQuery import Eq, Generic
from zope.interface import implements
from plone.memoize.instance import memoize, memoizedproperty
from Products.OpenPlans.content.project import OpenProject

_marker = object()

PAGENAME='projects-page-text'

class ProjectListingView(BrowserView):
    """
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.request.set('disable_border', 1)

    @memoizedproperty
    def catalog(self):
        return getToolByName(self.context, 'portal_catalog')
    
    @memoizedproperty
    def allprojects(self):
        path = '/'.join(self.context.getPhysicalPath())
        return self.catalog.evalAdvancedQuery(Generic('path', path) \
                                             & Eq('portal_type',
                                                  OpenProject.portal_type),
                                              (('sortable_title', 'asc'), ))
    @property
    def alpha(self):
        for a in "abcdefghijklmnopqrstuvwxyz":
            yield a
    
    @memoizedproperty
    def leftcolumn(self):
        """to simulate what happens in document_view
        """
        col = {'class':'plain',
               'txt':''}
        
        page = getattr(self.context,
                       PAGENAME, _marker)

        if page is _marker:
            return col

        fmt=('text/structured', 'text/x-rst')

        if page.Format() in fmt: col['class'] = 'stx'
        
        col['txt'] = page.CookedBody(stx_level=2)            
        return col
