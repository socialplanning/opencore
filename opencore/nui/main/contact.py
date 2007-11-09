from plone.memoize.view import memoize as req_memoize
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from opencore.browser.base import BaseView, _
from opencore.browser import formhandler
from opencore.nui.email_sender import EmailSender

class ContactView(BaseView, formhandler.OctopoLite):
    """
    View for the site admin contact form.
    """
    form_fields = ['sender_fullname', 'sender_from_address', 'subject',
                   'message']

    template = ZopeTwoPageTemplateFile('contact-site-admin.pt')

    @property
    @req_memoize
    def email_sender(self):
        return EmailSender(self)

    def validate(self):
        req = self.request
        for field in self.form_fields:
            if not req.form.get(field):
                self.errors[field] = 'Input required'
    
    @formhandler.action('send')
    def send(self, targets=None, fields=None):
        """
        Send an email to the site administrator with the text from the
        request form.
        """
        self.validate()
        if self.errors:
            # don't send, just return and render the page
            self.addPortalStatusMessage(u'psm_please_correct_errors', u'Please correct the specified '
                                        'errors.')
            return
        form = self.request.form
        mto = self.portal.getProperty('email_from_address')
        msg = form.get('message')
        subject = form.get('subject')
        mfrom = form.get('sender_from_address')
        self.email_sender.sendEmail(mto, msg=msg, subject=subject,
                                    mfrom=mfrom)
        self.addPortalStatusMessage(u'psm_message_sent_to_admin', u'Message sent.')
        self.template = None
        self.redirect(self.request.ACTUAL_URL)
