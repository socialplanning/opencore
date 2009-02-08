from opencore.nui.main.search import SearchView as BaseSearchView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class SearchView(BaseSearchView):
    
    _sortable_fields = ZopeTwoPageTemplateFile('searchresults-sortwidget.pt')

    def handle_request(self):
        cat = self.get_tool('portal_catalog')
        path = '/'.join(self.context.getPhysicalPath())
        results = cat(path=path, sort_on=self.sort_by)

        start = self.from_page(self.page, self.batch_size)
        results = self._get_batch(results, start, size=self.batch_size)

        return results
