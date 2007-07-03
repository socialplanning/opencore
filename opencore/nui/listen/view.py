from opencore.listen.mailinglist_views import MailingListAddForm, MailingListEditForm
from Products.listen.browser.mailinglist_views import MailingListView
from Products.listen.browser.mail_archive_views import ArchiveForumView, ArchiveDateView, ArchiveNewTopicView
from opencore.nui.base import BaseView


def make_nui_listen_view_class(cls, set_errors=False):
    class NuiListenView(BaseView, cls):
        def __init__(self, context, request):
            BaseView.__init__(self, context, request)
            cls.__init__(self, context, request)
            if set_errors:
                self.errors = ()
    return NuiListenView

NuiMailingListView      = make_nui_listen_view_class(MailingListView)
NuiMailingListAddView   = make_nui_listen_view_class(MailingListAddForm, set_errors=True)
NuiMailingListEditView  = make_nui_listen_view_class(MailingListEditForm, set_errors=True)
NuiArchiveForumView     = make_nui_listen_view_class(ArchiveForumView)
NuiArchiveDateView      = make_nui_listen_view_class(ArchiveDateView)
NuiArchiveNewTopicView  = make_nui_listen_view_class(ArchiveNewTopicView)
