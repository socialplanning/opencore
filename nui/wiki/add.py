from Products.wicked.browser.add import WickedAdd
from Acquisition import aq_inner
from Products.wicked.lib.normalize import titleToNormalizedId as normalize
from zope.interface import providedBy
from zope.app.apidoc.component import getRequiredAdapters as get_required
from zope.publisher.interfaces import IRequest
from opencore.nui.base import BaseView
import itertools


class NuiWickedAdd(WickedAdd):
    type_name = 'OpenPage'
    _viewnames = None
    reserved = []
    extender = 'page'

    @property
    def names_for_context(self):
        return get_view_names(self.context) | set(self.reserved)
        
    def sanitize(self, id_):
        new_id = normalize(id_)
        if new_id in self.names_for_context:
            new_id = "%s-%s" %(new_id, self.extender)
        return new_id
        
    def add_content(self, title=None, section=None):
        # this is 2.5 specific and will need to be updated for new
        # wicked implementation (which is more modular)
        title = self.request.get('Title', title)
        section = self.request.get('section', section)
        assert title, 'Must have a title to create content' 
        newcontentid=self.sanitize(title)
        parent = aq_inner(self.context).aq_parent
        parent.invokeFactory(self.type_name, id=newcontentid,
                             title=title)

        newcontent = getattr(self.context, newcontentid)
        wicked = getFilter(self.context)
        wicked.section=section
        wicked.manageLink(newcontent, title)

        portal_status_message='"%s" has been created' % title
        BaseView.add_status_message(self, portal_status_message)
        url = newcontent.absolute_url()
        restr = "%s/edit" %url
        return BaseView.redirect(self, restr)

def get_view_names(obj):
    provided = providedBy(obj)
    regs = itertools.chain(*(get_required(iface, withViews=True) \
                             for iface in provided))
    return set(reg.name for reg in regs if reg.required[-1].isOrExtends(IRequest))
        
