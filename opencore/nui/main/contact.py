from Products.CMFCore.utils import getToolByName

from opencore.browser.base import BaseView, _
from opencore.nui.email_sender import EmailSender

from zope.app.form.browser.textwidgets import TextWidget
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.formlib.formbase import form
from Products.Five.formlib.formbase import PageForm
from zope import schema

class ContactHiddenWidget(TextWidget):
    """the value gets dynamically inserted by the create_hidden_widget function
       below"""
    type = 'hidden'

    def _getFormValue(self):
        #the value gets dynamically inserted at runtime by the
        # create_hidden_widget function
        return self.value

def create_hidden_widget(value):
    return type('HiddenWidget', (ContactHiddenWidget,), dict(value=value))

class ContactView(PageForm, BaseView):
    """
    View for the site admin contact form.
    """

    form_fields = form.FormFields(
        schema.TextLine(title=u'Fullname', description=u'Full name of sender', __name__='sender_fullname', required=False),
        schema.TextLine(title=u'Email', description=u'Email address of sender', __name__='sender_from_address', required=True),
        schema.TextLine(title=u'Subject', description=u'Subject of email', __name__='subject', required=True),
        schema.Choice(title=u'Question', description=u'Inquiry question', __name__='question', required=True,
                      values=[
                            u"I'm experiencing trouble with the website",
                            u"I'd like to request a new feature or tool",
                            u"I'd like to report a bug",
                            u"I have a non-technical question",
                            ]),
        schema.Text(title=u'Message', description=u'Content of email inquiry', __name__='message', required=True))

    prefix = u''
    label = u'Contact the site administrator'

    template = ViewPageTemplateFile('contact-site-admin.pt')

    def setUpWidgets(self, ignore_request=False):
        # we have special logic here if the user is authenticated
        # we convert the fullname and email address widgets into hidden fields
        mstool = getToolByName(self.context, 'portal_membership')
        if not mstool.isAnonymousUser():
            mem = mstool.getAuthenticatedMember()
            self.form_fields['sender_fullname'].custom_widget = (
                create_hidden_widget(mem.fullname))
            self.form_fields['sender_from_address'].custom_widget = (
                create_hidden_widget(mem.email))
        return super(ContactView, self).setUpWidgets(ignore_request=ignore_request)

    @form.action(u'Send', prefix=u'')
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
