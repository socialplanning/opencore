"""
views pertaining to accounts -- creation, login, password reset
"""
import logging
from opencore.account.browser import AccountView
from opencore.browser.base import BaseView, _
from opencore.browser.formhandler import * # start import are for pansies
from opencore.member.interfaces import IHandleMemberWorkflow
from plone.memoize import instance
import urllib

logger = logging.getLogger("opencore.account.confirmation")
    
class ConfirmAccountView(AccountView):

    @property
    def key(self):
        return self.request.form.get('key', '')
    
    @instance.memoizedproperty
    def member(self):
        member = None
        try:
            UID, confirmation_key = self.key.split('confirm')
        except ValueError: # if there is no 'confirm' (or too many?)
            return None
    
        # we need to do an unrestrictedSearch because a default search
        # will filter results by user permissions
        matches = self.membranetool.unrestrictedSearchResults(UID=UID)
        if matches:
            member = matches[0].getObject()
            if member._confirmation_key == confirmation_key:
                return member
        return None

    def confirm(self, member):
        """Move member into the confirmed workflow state"""
        member = IHandleMemberWorkflow(member)
        if not member.is_unconfirmed():
            self.addPortalStatusMessage(_(u'psm_not_pending_account',
                                          u'You have tried to activate an account that is not pending confirmation. Please sign in normally.'))
            return False

        member.confirm()
        return True
        
    def handle_confirmation(self, *args, **kw):
        member = self.member
        if member is None:
            self.addPortalStatusMessage(_(u'psm_denied', u'Denied -- bad key'))
            return self.redirect("%s/%s" %(self.siteURL, 'login'))
        
        # redirect to login page if confirmation isn't pending
        if not self.confirm(member):
            return self.redirect("%s/login" %self.siteURL)

        self.login(member.getId())
        return self.redirect("%s/init-login" %self.siteURL)

class PendingView(AccountView):

    def _pending_member(self):
        key = self.request.form.get('key')
        unauthorized_destination = self.siteURL
        if not key:
            self.redirect(unauthorized_destination)
        member = self.is_pending(UID=key)
        if not member:
            self.redirect(unauthorized_destination)
        return member

    @post_only(raise_=False)    
    def handle_post(self):
        member = self._pending_member()
        if not member:
            return

        email = ''
        if self.request.form.get('resend_email'):
            email = member.getEmail()

        if self.request.form.get('new_email'):
            email = self.request.form.get('email', '')
            msg = member.validate_email(email)
            if msg:
                email = ''
            else:
                member.setEmail(email)
        
        mem_name = member.getFullname()
        mem_name = mem_name or member.getId()

        if email:
            self._send_mail_to_pending_user(mem_name,
                                            email,
                                            self._confirmation_url(member))
            mfrom = self.portal.getProperty('email_from_address')
            msg = _(u'psm_new_activation', mapping={u'email':email, u'mfrom':mfrom})

        self.addPortalStatusMessage(msg)

    def handle_request(self):
        self._pending_member()


class ResendConfirmationView(AccountView):

    @anon_only(BaseView.siteURL)
    def handle_request(self):
        name = self.request.form.get('member', '')
        member = self.is_pending(getUserName=name)
        if not member:
            self.add_status_message('No pending member by the name "%s" found' % name)
            self.redirect(self.siteURL)
            return
        mem_name = member.getFullname()
        mem_name = mem_name or member.getId()
        email = member.getEmail()
        mfrom = self.portal.getProperty('email_from_address')
        self._send_mail_to_pending_user(mem_name,
                                        email,
                                        self._confirmation_url(member))
        self.addPortalStatusMessage(_(u'psm_new_activation', mapping={u'email':email, u'mfrom':mfrom}))
        self.redirect("%s/login" %self.siteURL)













