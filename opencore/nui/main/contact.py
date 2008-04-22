from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.formlib.formbase import form
from Products.Five.formlib.formbase import PageForm

from opencore.browser.base import BaseView, _
from opencore.nui.email_sender import EmailSender

from zope.app.form.browser import TextWidget
from zope import schema
from zope.app.form import CustomWidgetFactory

import re

class NotAnEmailAddress(schema.ValidationError):
    __doc__ = _(u'contact-site-admin_email_validation_error',
                u'This is not a valid email address')
    
email_regex = r"[a-zA-Z0-9._%-]+@([a-zA-Z0-9-]+\.)*[a-zA-Z]{2,4}"
check_email = re.compile(email_regex).match
def validate_email(value):
    if not check_email(value):
        raise NotAnEmailAddress(value)
    return True

class ContactHiddenWidget(TextWidget):
    """Custom widget that displays itself as a hidden widget
       if authenticated.
       Note that the custom widget factory is responsible for adding the
       loggedin and value properties"""

    def _getFormValue(self):
        if self.loggedin:
            return self.value
        else:
            return super(ContactHiddenWidget, self)._getFormValue()

class ContactView(PageForm, BaseView):
    """
    View for the site admin contact form.
    """

    form_fields = form.FormFields(
        schema.TextLine(title=_(u'contact-site-admin_label_sender_fullname', u'Name'),
                        description=u'Full name of sender',
                        __name__='sender_fullname',
                        required=False),
        schema.TextLine(title=_(u'contact-site-admin_label_sender_from_address', u'Email'),
                        description=u'Email address of sender',
                        __name__='sender_from_address',
                        constraint=validate_email,
                        required=True),
        schema.TextLine(title=_(u'contact-site-admin_label_subject', u'Subject'),
                        description=u'Subject of email',
                        __name__='subject',
                        required=True),
        schema.Choice(title=_(u'contact-site-admin_label_question', u'Question'),
                      description=u'Inquiry question',
                      __name__='question',
                      required=True,
                      values=[
                            u"I'm experiencing trouble with the website",
                            u"I'd like to request a new feature or tool",
                            u"I'd like to report a bug",
                            u"I have a non-technical question",
                            ]),
        schema.Text(title=_(u'contact-site-admin_label_message', u'Message'),
                    description=u'Content of email inquiry',
                    __name__='message',
                    required=True))

    prefix = u''
    label = u'Contact the site administrator'

    template = ViewPageTemplateFile('contact-site-admin.pt')

    def _create_widget(self, value_getter):
        mstool = getToolByName(self.context, 'portal_membership')
        loggedin = not mstool.isAnonymousUser()
        if loggedin:
            mem = mstool.getAuthenticatedMember()
            type = 'hidden'
            value = value_getter(mem)
        else:
            type = 'text'
            value = None
        return CustomWidgetFactory(ContactHiddenWidget,
                                   type=type,
                                   loggedin=loggedin,
                                   value=value)

    def setUpWidgets(self, ignore_request=False):
        # we have special logic here if the user is authenticated
        # we convert the fullname and email address widgets into hidden fields

        self.form_fields['sender_fullname'].custom_widget = (
            self._create_widget(value_getter=lambda mem:mem.fullname))
        self.form_fields['sender_from_address'].custom_widget = (
            self._create_widget(value_getter=lambda mem:mem.email))

        return super(ContactView, self).setUpWidgets(ignore_request=ignore_request)

    @form.action(_(u'label_send', u'Send'), prefix=u'')
    def send(self, action, data):
        """
        Send an email to the site administrator with the text from the
        request form.
        """
        fullname = data['sender_fullname']
        mfrom = data['sender_from_address']
        subject = data['subject']
        question = data['question']
        message = data['message']
        mto = self.portal.getProperty('email_from_address')

        msg = ('Name -> %(name)s\nQuestion -> %(question)s\n\n%(message)s' %
               dict(name=fullname, question=question, message=message))

        EmailSender(self).sendEmail(mto, msg=msg, subject=subject, mfrom=mfrom)
        self.addPortalStatusMessage(_(u'psm_message_sent_to_admin', u'Message sent.'))
        self.redirect(self.portal.absolute_url())
