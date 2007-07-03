from opencore.listen.mailinglist_views import MailingListAddForm, MailingListEditForm
from Products.listen.browser.mailinglist_views import MailingListView
from Products.listen.browser.mail_archive_views import ArchiveForumView, ArchiveDateView
from opencore.nui.base import BaseView

class NuiMailingListView(BaseView, MailingListView):
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        MailingListView.__init__(self, context, request)
        self.errors = ()

class NuiMailingListAddView(BaseView, MailingListAddForm):
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        MailingListAddForm.__init__(self, context, request)
        self.errors = ()

class NuiMailingListEditView(BaseView, MailingListEditForm):
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        MailingListEditForm.__init__(self, context, request)
        self.errors = ()

class NuiArchiveForumView(BaseView, ArchiveForumView):
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        ArchiveForumView.__init__(self, context, request)
        self.errors = ()

class NuiArchiveDateView(BaseView, ArchiveDateView):
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        ArchiveDateView.__init__(self, context, request)
        self.errors = ()
