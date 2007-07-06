from opencore.listen.mailinglist_views import MailingListAddForm, MailingListEditForm, MailingListView
from Products.listen.browser.mail_archive_views import ArchiveForumView, ArchiveDateView, \
                                                       ArchiveNewTopicView, SubFolderDateView
from Products.listen.browser.mail_message_views import ForumMailMessageView
from opencore.nui.base import BaseView


def make_nui_listen_view_class(ListenClass, set_errors=False):
    class NuiListenView(BaseView, ListenClass):
        def __init__(self, context, request):
            BaseView.__init__(self, context, request)
            ListenClass.__init__(self, context, request)
            if set_errors:
                self.errors = ()
    return NuiListenView


NuiMailingListView      = make_nui_listen_view_class(MailingListView)
NuiMailingListAddView   = make_nui_listen_view_class(MailingListAddForm, set_errors=True)
NuiMailingListEditView  = make_nui_listen_view_class(MailingListEditForm, set_errors=True)
NuiArchiveForumView     = make_nui_listen_view_class(ArchiveForumView)
NuiArchiveDateView      = make_nui_listen_view_class(ArchiveDateView)
NuiArchiveNewTopicView  = make_nui_listen_view_class(ArchiveNewTopicView)
NuiSubFolderDateView    = make_nui_listen_view_class(SubFolderDateView)

class NuiForumMailMessageView(BaseView, ForumMailMessageView):
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        ForumMailMessageView.__init__(self, context, request)

        # hack around alecm's "five acquisition nightmare" hack
        # see listen/browser/mail_message_views.py line 70
        self.kontext = None

    def setKontext(self, value):
        self.kontext = value

    def getKontext(self):
        return self.kontext

    context = property(getKontext, setKontext)
