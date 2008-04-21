from Products.CMFCore.utils import getToolByName

from opencore.browser.base import BaseView, _
from opencore.nui.email_sender import EmailSender

from zope.app.form.browser import TextWidget
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.formlib.formbase import form
from Products.Five.formlib.formbase import PageForm
from zope import schema
from zope.app.form import CustomWidgetFactory

class ContactHiddenWidget(TextWidget):
    """Custom widget that displays itself as a hidden widget
       with the class level 'value' as the input value"""
    
    type = 'hidden'

    def _getFormValue(self):
        #the value gets inserted by the custom widget factory
        return self.value

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

    def setUpWidgets(self, ignore_request=False):
        # we have special logic here if the user is authenticated
        # we convert the fullname and email address widgets into hidden fields
        mstool = getToolByName(self.context, 'portal_membership')
        if not mstool.isAnonymousUser():
            mem = mstool.getAuthenticatedMember()
            self.form_fields['sender_fullname'].custom_widget = (
                CustomWidgetFactory(TextWidget, value=mem.fullname))
            self.form_fields['sender_from_address'].custom_widget = (
                CustomWidgetFactory(TextWidget, value=mem.fullname))
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
