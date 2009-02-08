from opencore.nui.main.search import SearchView as BaseSearchView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class SearchView(BaseSearchView):
    
    _result_listing = ZopeTwoPageTemplateFile('searchresults-resultlist.pt')
    _sortable_fields = ZopeTwoPageTemplateFile('searchresults-sortablefields.pt')
    _sort_string = ZopeTwoPageTemplateFile('searchresults-sortstring.pt')

