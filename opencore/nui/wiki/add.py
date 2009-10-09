from Acquisition import aq_inner, aq_parent
from opencore.browser.base import BaseView
from opencore.browser.naming import get_view_names
from opencore.i18n import _
from wicked.at.link import ATWickedAdd as WickedAdd

# we have a local copy of the normalize module b/c the wicked trunk
# (which is a part of Plone 3 core) doesn't handle unicode as nicely
# as we'd like
from normalize import titleToNormalizedId as normalize

from wicked.utils import getWicked

from zExceptions import BadRequest
from zope.component import ComponentLookupError


class NuiBaseAdd(WickedAdd, BaseView):
    type_name = 'Document'
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
            wicked = getWicked(self.context.getField('text'), self.context)
            wicked.section=section 
            wicked.manageLink(newcontent, normalize(title))
        except ComponentLookupError:
            pass
        
    def add_content(self, title=None, section=None):
        # XXX rename, we're not adding any old content, it's a wiki page.
        title = self.request.get('Title', title)
        if title:
            title = title.decode("utf-8")
        section = self.request.get('section', section)
        assert title, 'Must have a title to create content' 
        newcontentid=self.sanitize(title)
        container = self.get_container()

        try:
            container.invokeFactory(self.type_name, id=newcontentid,
                             title=title)
        except BadRequest, e:
            self.add_status_message(_(u'psm_page_create-failed',
                                      u'Creating "${pagetitle}" has failed because ${reason}',
                                      mapping={'pagetitle': title, 'reason' : str(e)})
                                    )
            referrer = self.context.absolute_url()
            return self.redirect(referrer)

        newcontent = container[newcontentid]
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

