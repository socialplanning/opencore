from Products.Five.browser import metaconfigure
from Products.Five.browser import pagetemplatefile
from Products.PageTemplates.PageTemplate import PageTemplate
from Products.listen.browser.mail_archive_views import ArchiveForumView, ArchiveDateView
from Products.listen.browser.mail_archive_views import ArchiveNewTopicView, SubFolderDateView
from Products.listen.browser.mail_archive_views import ArchiveSearchView
from Products.listen.browser.mail_message_views import ForumMailMessageView, ThreadedMailMessageView
from Products.listen.browser.mail_message_views import MessageReplyView, SearchDebugView
from Products.listen.browser.manage_membership import ManageMembersView
from Products.listen.browser.moderation import ModerationView
from Products.listen.interfaces import IMailingList
from Products.listen.utilities.list_lookup import ListLookupView
from opencore.browser.base import BaseView
from opencore.listen.mailinglist_views import MailingListAddForm, MailingListEditForm, MailingListView
from plone.app.form import _named
from plone.memoize.view import memoize as req_memoize
from zope.formlib.namedtemplate import INamedTemplate
from zope.interface import implements
import cgi
import new
import os.path


class ListenBaseView(BaseView):
    @req_memoize
    def list_url(self):
        obj = self.context
        while not IMailingList.providedBy(obj):
            try:
                obj = obj.aq_parent
            except AttributeError:
                return ''
        return obj.absolute_url()            

    @req_memoize
    def list_title(self):
        obj = self.context
        while not IMailingList.providedBy(obj):
            try:
                obj = obj.aq_parent
            except AttributeError:
                return ''
        return obj.Title()            
        
    @property
    def portal_status_message(self):
        if hasattr(self, '_redirected'):
            return []
        plone_utils = self.get_tool('plone_utils')
        msgs = plone_utils.showPortalMessages()
        if msgs:
            msgs = [msg.message for msg in msgs]
        else:
            msgs = []
        req_psm = self.request.form.get("portal_status_message")
        req_psm2 = self.request.get("portal_status_message")
        if req_psm:
            req_psm = cgi.escape(req_psm)
            msgs.append(req_psm)
        elif req_psm2:
            req_psm2 = cgi.escape(req_psm2)
            msgs.append(req_psm2)

        return msgs

# uh.. if you are going right meta factories you should write tests too
def make_nui_listen_view_class(ListenClass, set_errors=False, add_update=False):
    class NuiListenView(ListenBaseView, ListenClass):
        # mask the property defined in any listen views
        context = None
        def __init__(self, context, request):
            self.context = context # MUST set context before calling the ListenClass constructor
            ListenClass.__init__(self, context, request)
            BaseView.__init__(self, context, request)

            psm = self.request.get('portal_status_message')
            
            if set_errors:
                self.errors = ()

        if add_update:
            def update(self):
                result = super(NuiListenView, self).update()
                if self.status and self.errors:
                    self.addPortalStatusMessage(self.status)
                return result

    return NuiListenView


NuiMailingListView = make_nui_listen_view_class(MailingListView)
NuiMailingListAddView = make_nui_listen_view_class(MailingListAddForm, set_errors=True, add_update=True)
NuiMailingListEditView = make_nui_listen_view_class(MailingListEditForm, set_errors=True, add_update=True)
NuiArchiveForumView = make_nui_listen_view_class(ArchiveForumView)
NuiArchiveDateView = make_nui_listen_view_class(ArchiveDateView)
NuiArchiveNewTopicView = make_nui_listen_view_class(ArchiveNewTopicView)
NuiSubFolderDateView = make_nui_listen_view_class(SubFolderDateView)
NuiThreadedMailMessageView = make_nui_listen_view_class(ThreadedMailMessageView)
NuiForumMailMessageView = make_nui_listen_view_class(ForumMailMessageView)
NuiMessageReplyView = make_nui_listen_view_class(MessageReplyView)
NuiManageMembersView = make_nui_listen_view_class(ManageMembersView)
NuiModerationView = make_nui_listen_view_class(ModerationView)
NuiSearchDebugView = make_nui_listen_view_class(SearchDebugView)
NuiArchiveSearchView  = make_nui_listen_view_class(ArchiveSearchView)
NuiListLookupView = make_nui_listen_view_class(ListLookupView)


##########################################################################
# We're overriding the default NamedTemplateAdapter to work around a
# bug in plone.app.form._named.  The bug has been fixed on the Plone
# trunk.
##########################################################################

class NamedTemplateAdapter(object):
    """A named template adapter implementation that has the ability
    to lookup the template portion from regular traversal (intended for
    being able to customize the template portion of a view component
    in the traditional portal_skins style).
    """

    implements(INamedTemplate)

    def __init__(self, context):
        self.context = context

    def __call__(self, *args, **kwargs):
        """
        use aq_inner of the innermost context so we don't get a
        circular acquisition context.
        """
        view = self.context.__of__(self.context.context.aq_inner)
        cleanup = []

        # basically this means we only do customized template lookups
        # for views defined with <browser:page template='foo'> 
        if isinstance(view, metaconfigure.ViewMixinForTemplates) and \
               _named.try_portal_skins:
            index = getattr(view, 'index', None)
            if index is not None:
                name = _named.proper_name(index.filename)
                try:
                    template = view.context.portal_url.getPortalObject().restrictedTraverse(name)
                except AttributeError:
                    # ok, we couldn't find a portal_skins defined item
                    # so we fall back to the defined page template
                    template = index
                else:
                    if isinstance(getattr(template, 'aq_base', object()), PageTemplate):
                        template = _named.ViewTemplateFromPageTemplate(template,
                                                                       view.context)
                        template = template.__of__(view)
                    else:
                        template = index

            result = template(*args, **kwargs)
            return result
        else:
            return self.default_template.__of__(view)(*args, **kwargs)


def named_template_adapter(template):
    """Return a new named template adapter which defaults the to given
    template.
    """

    new_class = new.classobj('GeneratedClass', 
                             (NamedTemplateAdapter,),
                             {})
    new_class.default_template = template

    return new_class

path_prefix = os.path.split(_named.__file__)[0]
_path = os.path.join(path_prefix, 'pageform.pt')
_template = pagetemplatefile.ViewPageTemplateFile(_path)
default_named_template_adapter = named_template_adapter(_template)

_subpage_path = os.path.join(path_prefix, 'subpageform.pt')
_subpage_template = pagetemplatefile.ViewPageTemplateFile(_subpage_path)
default_subpage_template = named_template_adapter(_subpage_template)
