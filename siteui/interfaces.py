from zope.interface import Interface, Attribute, implements
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.schema import ASCIILine, TextLine, List, Bool
from zope.i18nmessageid import MessageFactory
from zope.viewlet.interfaces import IViewletManager
from opencore.interfaces import IMemberFolder

_ = MessageFactory('opencore')

### Interfaces for viewlet managers

class IOpenPlansSkin(IDefaultBrowserLayer):
    """Skin for OpenPlans"""


class IPersonaltools(IViewletManager):
    """Viewlets for personal tools (e.g. breadcrumbs + croutons)"""


class INavigation(IViewletManager):
    """Viewlets for navigation"""


class IInterceptEdit(Interface):
    """
    Edit interceptor
    """
    def has_permission():
        """
        current user has permission to edit object
        """


class IMemberInfo(Interface):
    """
    Information about members and location
    """
    inMemberArea = Attribute("whether or not context is within any member's "
                             "home folder")
    inPersonalArea = Attribute("whether or not context is authenticated "
                               "member's home folder")
    inMemberObject = Attribute("whether or not context is within a member "
                               "object")
    inSelf = Attribute("whether or not context is authenticated member object")
    member = Attribute("member object corresponding to the context's member "
                       "folder or object, if it exists; None if not")


class IMemberHomePage(Interface):
    """ Marker interface for member homepages """


class IFirstLoginEvent(Interface):
    """ Interface for FirstLoginEvent """


# this is deprecated for the plonents version
class ITranslate(Interface):
    """
    provides basic access to translation services
    """
        
    def utranslate(msgid, mapping={}, default=None, domain='plone', target_language=None):
        """
        @return translated unicode string
        """
    
    def translate(msgid, mapping={}, default=None, domain='plone', target_language=None, escape_for_js=False):
        """
        @return string : translated, unicode if applicable
        """

#@@ remove for plone3
class ILiveSearch(Interface):

    legend_livesearch = Attribute('Legend / title for searchbox')
    label_no_results_found = Attribute('label text if no results')
    searchterms = Attribute('terms used in search')
    query = Attribute('query used in search')
    limit = Attribute('how many results to show')
    
    def _getResults(query):
        """
        @return LazyMap : query the catalog
        """

    def results():
        """
        @return list : result set after limit or batching
        """

    def getResData(result):
        """
        @param result : a catalog brain
        @return dict
        
        getResData extracts data necessary for template from
        a catalog brain
        """
        
    def more():
        """
        @return boolean :  true if batch or results exceed limit
        """

    def getTitle(brain):
        """
        @return dict : contains display_title and fulltitle
        """


class IAddOpenPlans(Interface):
    """Add form for topp site"""

    id = ASCIILine(
        title=_(u"Id"),
        description=_(u"The object id."),
        default='openplans',
        required=True
        )
    
    title = TextLine(
        title=_(u"Title"),
        description=_(u"Name of the site instance"),
        default=u"OpenPlans",
        required=True
        )

    testcontent = Bool(
        title=_("Create test content"),
        description=_(u"Please create example projects and members"),
        default=False,
        required=False
        )
