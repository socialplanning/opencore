from opencore.listen.mailinglist_views import MailingListAddForm, MailingListEditForm, MailingListView
from Products.listen.browser.mail_archive_views import ArchiveForumView, ArchiveDateView, ArchiveNewTopicView
from Products.listen.browser.mail_message_views import ForumMailMessageView
from opencore.nui.base import BaseView


def make_nui_listen_view_class(cls, set_errors=False, set_context=False):
    class NuiListenView(BaseView, cls):
        def __init__(self, context, request):
            BaseView.__init__(self, context, request)
            cls.__init__(self, context, request)
            if set_errors:
                self.errors = ()

            # hack around alecm's "five acquisition nightmare" hack
            # see listen/browser/mail_message_views.py line 70
            self.kontext = None

        def setKontext(self, value):
            self.kontext = value

        def getKontext(self):
            return self.kontext

        context = property(getKontext, setKontext)

    return NuiListenView

NuiMailingListView      = make_nui_listen_view_class(MailingListView)
NuiMailingListAddView   = make_nui_listen_view_class(MailingListAddForm, set_errors=True)
NuiMailingListEditView  = make_nui_listen_view_class(MailingListEditForm, set_errors=True)
NuiArchiveForumView     = make_nui_listen_view_class(ArchiveForumView)
NuiArchiveDateView      = make_nui_listen_view_class(ArchiveDateView)
NuiArchiveNewTopicView  = make_nui_listen_view_class(ArchiveNewTopicView)
NuiForumMailMessageView = make_nui_listen_view_class(ForumMailMessageView)
