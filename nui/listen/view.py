from opencore.listen.mailinglist_views import MailingListAddForm, MailingListEditForm
from Products.listen.browser.mailinglist_views import MailingListView
from opencore.nui.base import BaseView

class OpenMailingListView(BaseView, MailingListView):
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        MailingListView.__init__(self, context, request)
        self.errors = ()

class MailingListAddView(BaseView, MailingListAddForm):
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        MailingListAddForm.__init__(self, context, request)
        self.errors = ()

class MailingListEditView(BaseView, MailingListEditForm):
    def __init__(self, context, request):
        BaseView.__init__(self, context, request)
        MailingListEditForm.__init__(self, context, request)
        self.errors = ()
