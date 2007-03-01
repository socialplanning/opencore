from zope.formlib import form
from zope.app.form.browser import ASCIIWidget

from Products.listen.browser.mailinglist_views import DescriptionWidget
from Products.listen.browser.mailinglist_views import MailingListAddForm

from interfaces import IOpenMailingList
from widgets import OpenListNameWidget

class MailingListAddForm(MailingListAddForm):
    """
    A form for adding OpenMailingList objects.
    """
    form_fields = form.FormFields(IOpenMailingList)
    form_fields['description'].custom_widget = DescriptionWidget
    form_fields['mailto'].custom_widget = OpenListNameWidget

    portal_type = 'Open Mailing List'
        
