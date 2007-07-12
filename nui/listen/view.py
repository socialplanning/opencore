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

def make_nui_listen_view_class(ListenClass, set_errors=False):
    class NuiListenView(BaseView, ListenClass):
        # mask the property defined in any listen views
        context = None
        def __init__(self, context, request):
            self.context = context # MUST set context before calling the ListenClass constructor
            ListenClass.__init__(self, context, request)
            BaseView.__init__(self, context, request)
            if set_errors:
                self.errors = ()

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
        

    return NuiListenView


NuiMailingListView = make_nui_listen_view_class(MailingListView)
NuiMailingListAddView = make_nui_listen_view_class(MailingListAddForm, set_errors=True)
NuiMailingListEditView = make_nui_listen_view_class(MailingListEditForm, set_errors=True)
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
