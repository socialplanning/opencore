from zope.formlib import form
from zope.app.form.browser import ASCIIWidget

from Products.listen.browser.mailinglist_views import DescriptionWidget
from Products.listen.browser.mailinglist_views import MailingListAddForm \
     as BaseAddForm
from Products.listen.browser.mailinglist_views import MailingListEditForm \
     as BaseEditForm
from Products.listen.browser.mailinglist_views import MailingListView

from interfaces import IOpenMailingList
from widgets import OpenListNameWidget

from Products.listen.browser.mailinglist_views import create_radio_widget
from Products.listen.browser.mailinglist_views import create_radio_widget
from Products.listen.browser.listwidget.widget import DynamicListWidget

openplans_form_fields = form.FormFields(IOpenMailingList)
openplans_form_fields['description'].custom_widget = DescriptionWidget
openplans_form_fields['mailto'].custom_widget = OpenListNameWidget
openplans_form_fields['archived'].custom_widget = create_radio_widget
openplans_form_fields['list_type'].custom_widget = create_radio_widget
openplans_form_fields['managers'].custom_widget = DynamicListWidget

class MailingListAddForm(BaseAddForm):
    """
    A form for adding OpenMailingList objects.
    """
    form_fields = openplans_form_fields
    portal_type = 'Open Mailing List'

    def __call__(self):
        """
        Disable editable border.
        """
        self.request.set('disable_border', True)
        return BaseAddForm.__call__(self)

class MailingListEditForm(BaseEditForm):
    """A form for editing MailingList objects.

    """
    form_fields = openplans_form_fields
