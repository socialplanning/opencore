from Products.validation.validators.BaseValidators import EMAIL_RE
from plone.memoize.view import memoize as req_memoize
from opencore.browser.base import BaseView
from opencore.browser import formhandler
from opencore.i18n import _
from opencore.utility.interfaces import IEmailSender
import re


email_regex = re.compile(EMAIL_RE)

#XXX this would be easier if moved to formlib
class ContactView(BaseView, formhandler.OctopoLite):
    """
    View for the site admin contact form.
    """
    form_fields = ['sender_fullname', 'sender_from_address', 'subject',
                   'message']

    questions = [
        u"I'm experiencing trouble with the website",
        u"I'd like to request a new feature or tool",
        u"I'd like to report a bug",
        u"I have a non-technical question",
        ]

    @property
    @req_memoize
    def email_sender(self):
        return IEmailSender(self.portal)

    def validate(self):
        form = self.request.form
        for field in self.form_fields:
            value = form.get(field, '').strip()
            if not value:
                self.errors[field] = 'Input required'
            form[field] = value
        email = form.get('sender_from_address', '')
        if email and not email_regex.match(email):
            self.errors['sender_from_address'] = 'Invalid email address'

    @formhandler.action('send')
    def send(self, targets=None, fields=None):
        """
        Send an email to the site administrator with the text from the
        request form.
        """
        self.validate()
        if self.errors:
            # don't send, just return and render the page
            self.addPortalStatusMessage(_(u'psm_please_correct_errors',
                                          u'Please correct the specified errors.'))
            return
        form = self.request.form
        mto = self.portal.getProperty('email_from_address')
        if form.get('question'):
            msg = form.get('question') + "\n\n--------------------\n[Message]:\n\n" + form.get('message')
        else:
            msg = form.get('message')
        subject = form.get('subject')
        mfrom = form.get('sender_from_address')
        # XXX we require sender_fullname but we ignore it! duh.
        self.email_sender.sendMail(mto, msg=msg, subject=subject,
                                   mfrom=mfrom)
        self.addPortalStatusMessage(_(u'psm_message_sent_to_admin', u'Message sent.'))
        self.index = None
        self.redirect(self.portal.absolute_url())
