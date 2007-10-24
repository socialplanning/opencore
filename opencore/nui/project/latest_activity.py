from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from opencore.nui.project.latest_snippet import LatestSnippet
from opencore.nui.project.view import ProjectContentsView


class ListFromCatalog:
    """
    return the latest items from a catalog
    """

    keys = [ 'portal_type', 'path' ]

    def __init__(self, portal_type, path):
        self.base_query = dict([(key, locals()[key]) for key in self.keys])

    def query(self):        
        return dict(sort_order='descending',
                    sort_on='Date', **self.base_query)

    def __call__(self, catalog, number=None):
        items = catalog(**self.query())
        if number is None:
            number = len(items)
        return items[:number]

class LatestActivityView(ProjectContentsView):
    """
    displays latest activity for a project.
    This is a concept class (sandbox) for the time being
    I think/hope the appropriate architecture will
    emerge from playing with it
    """

    # XXX this is necessary because the ProjectContentsView stupidly overrides template
    template = ZopeTwoPageTemplateFile('latest_activity.pt')

    def __init__(self, context, request):
        ProjectContentsView.__init__(self, context, request)
        self.feed_types = [ 'pages', 'lists' ]

    def feeds(self):
        return [ ListFromCatalog(self._portal_type['pages'], self.project_path)(self.catalog),
                 ListFromCatalog(self._portal_type['lists'], self.project_path)(self.catalog) ]

    def activity(self):
        f = ListFromCatalog(portal_type='Document', path=self.project_path)
        g = LatestSnippet(self.context, self.request, 'A Bad Title')
        import pdb;  pdb.set_trace()
            
