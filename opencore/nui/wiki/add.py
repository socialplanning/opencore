from Products.wicked.browser.add import WickedAdd
from Acquisition import aq_inner, aq_parent
from Products.wicked.lib.normalize import titleToNormalizedId as normalize

from opencore.browser.base import BaseView
from opencore.browser.base import _
from Products.wicked.utils import getFilter
from zope.component import ComponentLookupError
from zExceptions import Redirect
import itertools


class NuiBaseAdd(WickedAdd, BaseView):
    type_name = 'Document'
    _viewnames = None
    extender = 'page'

    def __init__(self, context, request):
        super(NuiBaseAdd, self).__init__(context, request)
        self.errors = {}
        self.response = self.request.RESPONSE
    
    def get_container(self):
        raise NotImplementedError

    def sanitize(self, id_):
        new_id = normalize(id_)
        if new_id in self.names_for_context:
            new_id = "%s-%s" %(new_id, self.extender)
        return new_id
    
    def do_wicked(self, newcontent, title, section):
        try:
            wicked = getFilter(self.context)
            wicked.section=section 
            wicked.manageLink(newcontent, normalize(title))
        except ComponentLookupError:
            pass
        
    def add_content(self, title=None, section=None):
        # this is 2.5 specific and will need to be updated for new
        # wicked implementation (which is more modular)
        title = self.request.get('Title', title)
        if title:
            title = title.decode("utf-8")
        section = self.request.get('section', section)
        assert title, 'Must have a title to create content' 
        newcontentid=self.sanitize(title)
        container = self.get_container()
        container.invokeFactory(self.type_name, id=newcontentid,
                             title=title)
        newcontent = getattr(self.context, newcontentid)
        self.do_wicked(newcontent, title, section)
        self.add_status_message(_(u'psm_page_created',
                                  u'"${pagetitle}" has been created',
                                  mapping={'pagetitle': title})
                                )
        url = newcontent.absolute_url()
        restr = "%s/edit" %url
        return self.redirect(restr)

    @property
    def names_for_context(self):
        return get_view_names(self.get_container()) 


class NuiContainerAdd(NuiBaseAdd):
    """add mechanism for a container"""

    def get_container(self):
        return aq_inner(self.context)


class NuiPageAdd(NuiBaseAdd):

    def get_container(self):
        return aq_parent(aq_inner(self.context))

# consider moving out to more general location
# the project create code shares this as well
from zope.interface import providedBy
from zope.app.apidoc.component import getRequiredAdapters as get_required
from zope.publisher.interfaces import IRequest

def get_view_names(obj, ignore_dummy=False):
    """Gets all view names for a particular object"""
    ifaces = providedBy(obj)
    regs = itertools.chain(*(get_required(iface, withViews=True) \
                             for iface in ifaces))
    if ignore_dummy:
        return set(reg.name for reg in regs\
               if reg.required[-1].isOrExtends(IRequest) and not issubclass(reg.value, IgnorableDummy))
    return set(reg.name for reg in regs\
               if reg.required[-1].isOrExtends(IRequest))


class Dummy(BaseView):
    """Creates dummy for blocking the overcreation of deliverance
    paths"""

    def __init__(self, context, request):
        super(Dummy, self).__init__(context, request)
        
    def __call__(self, *args, **kw):
        raise Redirect, self.redirect_url

    @property
    def redirect_url(self):
        return "%s/%s" %(self.area.absolute_url(), "preferences")
    


class IgnorableDummy(Dummy):
    """a dummy that get_view_names will ignore (for special persistent objects)"""
    

    
    

