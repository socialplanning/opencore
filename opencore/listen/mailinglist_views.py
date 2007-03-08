from zope.formlib import form
from zope.app.form.browser import ASCIIWidget

from Products.listen.browser.mailinglist_views import DescriptionWidget
from Products.listen.browser.mailinglist_views import MailingListAddForm \
     as BaseAddForm
from Products.listen.browser.mailinglist_views import MailingListEditForm \
     as BaseEditForm

from interfaces import IOpenMailingList
from widgets import OpenListNameWidget

from Products.listen.browser.mailinglist_views import ArchiveListWidget
from Products.listen.browser.mailinglist_views import ListTypeListWidget



class MailingListAddForm(BaseAddForm):
    """
    A form for adding OpenMailingList objects.
    """
    form_fields = form.FormFields(IOpenMailingList)
    form_fields['description'].custom_widget = DescriptionWidget
    form_fields['mailto'].custom_widget = OpenListNameWidget
    form_fields['archived'].custom_widget = ArchiveListWidget
    form_fields['list_type'].custom_widget = ListTypeListWidget
    portal_type = 'Open Mailing List'


class MailingListEditForm(BaseEditForm):
    """A form for editing MailingList objects.

    """
    form_fields = form.FormFields(IOpenMailingList)
    form_fields['description'].custom_widget = DescriptionWidget
    form_fields['mailto'].custom_widget = OpenListNameWidget
    form_fields['archived'].custom_widget = ArchiveListWidget
    form_fields['list_type'].custom_widget = ListTypeListWidget
