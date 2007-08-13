from opencore.listen.mailinglist_views import MailingListAddForm, MailingListEditForm, MailingListView
from Products.listen.browser.mail_archive_views import ArchiveForumView, ArchiveDateView, \
                                                       ArchiveNewTopicView, SubFolderDateView, \
                                                       ArchiveSearchView
from Products.listen.browser.mail_message_views import ForumMailMessageView, ThreadedMailMessageView, \
                                                       MessageReplyView, SearchDebugView
from Products.listen.browser.manage_membership import ManageMembersView
from Products.listen.utilities.list_lookup import ListLookupView
from Products.listen.browser.moderation import ModerationView
from opencore.nui.base import BaseView
from Products.listen.interfaces import IMailingList
from plone.memoize.view import memoize as req_memoize
import cgi


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
