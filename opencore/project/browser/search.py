from opencore.nui.main.search import SearchView

class ProjectWikiSearchView(SearchView):

    def handle_request(self):
        cat = self.get_tool('portal_catalog')
        path = '/'.join(self.context.getPhysicalPath())
        results = cat(path=path, sort_on=self.sort_by,
                      SearchableText=self.request.get("q"))
        return results        
        
