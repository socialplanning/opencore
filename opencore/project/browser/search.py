from opencore.nui.main.search import SearchView as BaseSearchView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class SearchView(BaseSearchView):
    
    _sortable_fields = ZopeTwoPageTemplateFile('searchresults-sortwidget.pt')

