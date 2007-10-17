"""
livesearch view
"""
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from zope.interface import implements
from interfaces import ITranslate
from Products.Five.traversable import FakeRequest

def quotestring(s):
    return '"%s"' % s

def quote_bad_chars(s):
    bad_chars = ["(", ")"]
    for char in bad_chars:
        s = s.replace(char, quotestring(char))
    return s

# SIMPLE CONFIGURATION
LIMIT=10
USE_ICON = True
USE_RANKING = False
MAX_TITLE = 29
MAX_DESCRIPTION = 93
#DEFAULT_LEGEND = 'LiveSearch &darr;'
DEFAULT_LEGEND = 'jump'

class LiveSearch(BrowserView):

    query = None
    searchterms = None
    legend_livesearch = None
    label_no_results_found = None
    limit = LIMIT

    def __init__(self, context, REQUEST):
        self.context = context
        self.request = REQUEST
        self.limit = self.request.get('limit', self.limit)
        ploneUtils = getToolByName(context, 'plone_utils')
        self.pretty_title_or_id = ploneUtils.pretty_title_or_id
        portalProperties = getToolByName(context, 'portal_properties')
        siteProperties = getattr(portalProperties, 'site_properties', None)

        if siteProperties is not None:
            uva = siteProperties.getProperty('typesUseViewActionInListings', [])
            self.useViewAction = dict([(pt, None) for pt in uva])

        # generate a result set for the query
        self.catalog = getToolByName(context, 'portal_catalog')
        self.friendly_types = ploneUtils.getUserFriendlyTypes()

        # for now we just do a full search to prove a point, this is not the
        # way to do this in the future, we'd use a in-memory probability based
        # result set.
        # convert queries to zctextindex
        query=self.request.get('q', '').split(' ')
        query = " AND ".join(query)
        self.query = query and quote_bad_chars(query)+'*' or query
        
        self.searchterms = searchterms = self.query.replace(' ','+')

        translate = ITranslate(context)
        self.legend_livesearch = translate('legend_livesearch', default=DEFAULT_LEGEND)
        self.label_no_results_found = translate('label_no_results_found', default='No matching results found.')

        RESPONSE = self.context.REQUEST.RESPONSE
        RESPONSE.setHeader('Content-Type', 'text/xml;charset=%s' % ploneUtils.getSiteEncoding())

    def getResData(self, result):
        resdata = self.getTitle(result)
        itemURL = result.getURL()
        itemURL = self.useViewAction.get(result.portal_type, None) and  itemURL + '/view' or itemURL

        display_description = result.Description
        if len(display_description) >= MAX_DESCRIPTION:
            display_description = ''.join((display_description[:MAX_DESCRIPTION],'...'))
            
        resdata.update(dict(
            itemURL = itemURL,
            icon = result.getIcon,
            score = '%s%%' %result.data_record_normalized_score_,
            display_description=display_description
            ))
        
        return resdata
        
    def getTitle(self, brain):
        full_title = self.pretty_title_or_id(brain)
        if len(full_title) >= MAX_TITLE:
            display_title = ''.join((full_title[:MAX_TITLE],'...'))
        else:
            display_title = full_title
        return dict(display_title=display_title, full_title=full_title)

    def more(self):
        return self._lenresults>self.limit

    def _getResults(self, query):
        return self.catalog(SearchableText=query, portal_type=self.friendly_types)
        
    def results(self):
        self._results = self._getResults(self.query)
        self._lenresults = len(self._results)
        return self._results[:self.limit]
