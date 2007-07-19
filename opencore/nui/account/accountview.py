"""
views pertaining to accounts -- creation, login, password reset
"""
import urllib
import socket
from smtplib import SMTPRecipientsRefused, SMTP

from App import config
from AccessControl.SecurityManagement import newSecurityManager
from zExceptions import Forbidden, Redirect, Unauthorized

from zope.event import notify
from plone.memoize import instance

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.remember.utils import getAdderUtility
from Products.validation.validators.BaseValidators import EMAIL_RE

from opencore.siteui.member import FirstLoginEvent
from opencore.nui.base import BaseView
from opencore.nui.formhandler import *

class AccountView(BaseView):
    """
    base class for views dealing with accounts
    distinguished by its login functionality
    """

    add_status_message = BaseView.addPortalStatusMessage
    login_snippet = ZopeTwoPageTemplateFile('login_snippet.pt')
    forgot_snippet = ZopeTwoPageTemplateFile('forgot_snippet.pt')

    @property
    def auth(self):
        acl = self.get_tool("acl_users")
        return acl.credentials_signed_cookie_auth
    
    def login(self, member_id):
        """login a user programmatically"""
        self.update_credentials(member_id)
        self.request.set('__ac_name', member_id)
        self.auth.login()
        self.membertool.setLoginTimes()

    def update_credentials(self, member_id):
        return self.auth.updateCredentials(self.request, self.response,
                                           member_id, None)
    
    @property
    def login_url(self):
        return "%s/login" % self.context.absolute_url()

    @property
    def loggedin_fallback_url(self):
        """
        When a logged in user goes to the 'login' or 'forgot' page,
        go here instead. Used in conjunction with anon_only decorator.
        """
        return '%s/account' % self.memfolder_url()

    ### methods to deal with pending members

    def is_pending(self, **query):
        membrane_tool = self.get_tool('membrane_tool')
        matches = membrane_tool.unrestrictedSearchResults(**query)
        if len(matches) != 1:
            return
        member = matches[0].getObject()
        portal_workflow = self.get_tool('portal_workflow')
        if portal_workflow.getInfoFor(member, 'review_state') == 'pending':
            return member

    def _confirmation_url(self, mem):
        code = mem.getUserConfirmationCode()
        return "%s/confirm-account?key=%s" % (self.siteURL, code)

    def _sendmail_to_pendinguser(self, id, email, url):
        """ send a mail to a pending user """
        ## XX todo only send mail if in the pending workflow state
        mailhost_tool = getToolByName(self.context, "MailHost")

        mfrom = self.portal.getProperty('email_from_address')
        
        mailhost_tool.send("how are you %s?\ngo here: %s" % (id, url),
                           mto=email,
                           mfrom=mfrom,
                           subject='OpenPlans account registration')


class LoginView(AccountView):

    @button('login')
    @post_only(raise_=False)
    def handle_login(self):
        id_ = self.request.get('__ac_name')
        if self.loggedin:
            # check to see if the member is pending
            # XXX probably hack this off into its own function when refactoring
            # (above should again be modularized)
            member = None
            password = self.request.form.get('__ac_password')
            if id_ and password:
                member = self.is_pending(getId=id_)

            # ensure there is one match
            if member and member.verifyCredentials({'login': id_, 
                                                    'password': password}):
                
                self.addPortalStatusMessage('An email has been sent to %s from %s " \
                    "but it seems like you have not yet activated your account.' %
                    (member.getEmail(), self.portal.getProperty('email_from_address')))
                self.redirect('pending?key=%s' % member.UID())
                return

            self.addPortalStatusMessage('You are logged in')
            self.update_credentials(id_)
            self.membertool.setLoginTimes()

            # member area only created if it doesn't yet exist;
            # createMemberArea method will trigger
            # notifyMemberAreaCreated skin script, which will trigger
            # opencore.siteui.member.initializeMemberArea
            self.membertool.createMemberArea()

            member = self.loggedinmember
            try:
                if member.getLast_login_time() == member.getLogin_time():
                    # first login
                    notify(FirstLoginEvent(member, self.request))
            except AttributeError:
                # we're not a remember-based user
                pass

            destination = self.destination
            return self.redirect(destination)

        self.addPortalStatusMessage(u'Incorrect username or password. Please try again ' \
            'or <a href="forgot">retrieve your login information</a>.')

    @anon_only(AccountView.loggedin_fallback_url)
    def handle_request(self):
        pass
            
    @property
    def came_from(self):
        return self.request.get('came_from', '')

    def already_loggedin(self):
        if self.loggedin and self.request.get('loggedout'):
            return self.http_root_logout
        if self.loggedin:
            return True

    @property
    def destination(self):
        """where you go after you're logged in"""
        if self.came_from:
            destination = self.came_from 

            # append referer to destination as query string 
            # in order for insufficient_privileges to redirect correctly
            referer = self.request.form.get('referer')
            if referer is not None:
                destination = '%s?referer=%s' % (destination, 
                                                 urllib.quote(referer))
            return destination

        return '%s/account' % self.memfolder_url()

    def logout(self, redirect=None):
        logout = self.cookie_logout

        self.invalidate_session()
            
        self.add_status_message("You are logged out")
        
        if redirect is None:
            redirect = self.login_url
            
        self.redirect("%s?loggedout=yes" %redirect)

    @property
    def cookie_logout(self):
        self.context.acl_users.logout(self.request)
    
    @property
    def http_root_logout(self):
        raise Redirect("%s/manage_zmi_logout" %
                       self.context.getPhysicalRoot().absolute_url())
        
    def invalidate_session(self):
        # Invalidate existing sessions, but only if they exist.
        sdm = self.get_tool('session_data_manager')
        if sdm is not None:
            session = sdm.getSessionData(create=0)
        if session is not None:
            session.invalidate()

    def privs_redirect(self):
        self.add_status_message("Insufficient Privileges")
        if not self.loggedin:
            self.redirect(self.login_url)
            

class JoinView(AccountView, OctopoLite):

    template = ZopeTwoPageTemplateFile('join.pt')

    @action('join', apply=post_only(raise_=False))
    def create_member(self, targets=None, fields=None):
        context = self.context

        mdc = self.get_tool('portal_memberdata')
        mem = mdc._validation_member
        self.errors = {}
        self.errors = mem.validate(REQUEST=self.request,
                                   errors=self.errors,
                                   data=1, metadata=0)
        if self.errors:
            return self.errors

        # create a member in portal factory
        mdc = self.get_tool('portal_memberdata')
        pf = mdc.portal_factory

        #00 pythonscript call, move to fs code
        id_ = self.context.generateUniqueId('OpenMember')

        mem_folder = pf._getTempFolder('OpenMember')
        mem = mem_folder.restrictedTraverse('%s' % id_)

        # now we have mem, a temp member. create him for real.
        mem_id = self.request.form.get('id')
        mem = pf.doCreate(mem, mem_id)
        self.txn_note('Created %s with id %s in %s' % \
                      (mem.getTypeInfo().getId(),
                       mem_id,
                       self.context.absolute_url()))
        result = mem.processForm()
        url = self._confirmation_url(mem)

        if email_confirmation():
            self._sendmail_to_pendinguser(id=mem_id,
                                          email=self.request.get('email'),
                                          url=url)
            self.addPortalStatusMessage(u'An email has been sent to you, %s.' % mem_id)
            return mdc._getOb(mem_id)
        else:
            return self.redirect(url)

    @action('validate')
    def validate(self, targets=None, fields=None):
        """ this is really dumb. """
        mdc = self.get_tool('portal_memberdata')
        mem = mdc._validation_member
        errors = {}
        errors = mem.validate(REQUEST=self.request,
                              errors=self.errors,
                              data=1, metadata=0)
        erase = [error for error in errors if error not in self.request.form]
        also_erase = [field for field in self.request.form if field not in errors]
        for e in erase + also_erase:
            errors[e] = ''
        ret = {}
        for e in errors:
            ret['oc-%s-validator' % e] = {
                'html': str(errors[e]),
                'action': 'copy', 'effects': ''}
        return ret

    
class ConfirmAccountView(AccountView):

    @property
    def key(self):
        return self.request.form["key"]
    
    @instance.memoizedproperty
    def member(self):
        member = None
        
        try:
            UID = self.key
        except KeyError:
            return None
    
        # we need to do an unrestrictedSearch because a default search
        # will filter results by user permissions
        matches = self.membranetool.unrestrictedSearchResults(UID=UID)
        if matches:
            member = matches[0].getObject()
        return member

    def confirm(self, member):
        """Move member into the confirmed workflow state"""
        pf = self.get_tool("portal_workflow")
        if pf.getInfoFor(member, 'review_state') != 'pending':
            self.addPortalStatusMessage(u'Denied -- no confirmation pending')

            # use string interpolation pls
            return self.redirect("%s/login" %self.siteURL)
        
        setattr(member, 'isConfirmable', True)
        pf.doActionFor(member, 'register_public')
        delattr(member, 'isConfirmable')
        
    def handle_confirmation(self, *args, **kw):
        member = self.member
        if not member:
            self.addPortalStatusMessage(u'Denied -- bad key')
            return self.redirect("%s/%s" %(self.siteURL, 'login'))
        
        self.confirm(member)
        
        self.login(member.getId())
        return self.redirect("%s/init-login" %self.siteURL)


class InitialLogin(BaseView):

    def first_login(self):
        member = self.membertool.getAuthenticatedMember()
        if not self.membertool.getHomeFolder():
            self.membertool.createMemberArea(member.getId())
        baseurl = self.memfolder_url()
        # Go to the user's Profile Page in Edit Mode
        return self.redirect("%s/%s" % (self.memfolder_url(),
                                        'profile-edit?first_login=1'))


class ForgotLoginView(AccountView):

    @anon_only(AccountView.loggedin_fallback_url)
    @button('send')
    @post_only(raise_=False)
    def handle_request(self):
        userid = self.userid
        if userid:
            if email_confirmation():
                self._mailPassword(userid)
                self.addPortalStatusMessage('An email has been sent to you %s' % userid)
            else:
                self.redirect(self.reset_url)
            return True
        return False
    
    @instance.memoizedproperty
    def randomstring(self):
        pwt = self.get_tool("portal_password_reset")
        obj = pwt.requestReset(self.userid)
        return obj['randomstring']

    @property
    def reset_url(self):

        return '%s/reset-password?key=%s' % (self.siteURL, self.randomstring)
    
    def _mailPassword(self, forgotten_userid):
        if not self.membertool.checkPermission('Mail forgotten password', self):
            raise Unauthorized, "Mailing forgotten passwords has been disabled"

        member = self.membranetool(getId=forgotten_userid)

        if member is None:
            raise ValueError, 'The username you entered could not be found'
        
        member = member[0].getObject()
        
        email = member.getEmail()

        try:
            pwt = self.get_tool("portal_password_reset")
            mail_text = self.render_static("account_forgot_password_email.txt")
            mail_text += self.reset_url
            mfrom = self.portal.getProperty('email_from_address')            
            host = self.get_tool('MailHost')
            host.send(mail_text,
                      mfrom=mfrom,
                      subject='OpenPlans password reset',
                      mto=[email]
                      )
        except SMTPRecipientsRefused:
            # Don't disclose email address on failure
            raise SMTPRecipientsRefused('Recipient address rejected by server')

    @property
    def userid(self):
        user_lookup = self.request.get("__ac_name")
        if not user_lookup:
            self.addPortalStatusMessage(u"Please enter a user id or email address")
            return None
        
        if '@' in user_lookup:
            brains = self.membranetool(getEmail=user_lookup)
        else:
            brains = self.membranetool(getId=user_lookup)

        if not brains:
            self.addPortalStatusMessage(u"We can't find your account. This could be " \
                                         "because you have not yet completed your email " \
                                         "confirmation, or perhaps you just mistyped.")
            return
        return brains[0].getId


class PasswordResetView(AccountView):
    
    @button('set')
    @post_only(raise_=False)
    def handle_reset(self):
        password = self.request.get("password")
        password2 = self.request.get("password2")
        userid = self.request.get("userid")
        randomstring = self.request.get("key")

        # validate the password input
        if not self.validate_password_form(password, password2, userid):
            return False

        pw_tool = self.get_tool("portal_password_reset")
        try:
            pw_tool.resetPassword(userid, randomstring, password)
        except 'InvalidRequestError':
            # XXX TODO redirect to 404 instead
            return self.redirect(self.siteURL)
        except 'ExpiredRequestError':
            msg = u'Your password reset request has expired.'
            msg += (u'You can <a href="login">log in</a> again using'
                    'your old username and password or '
                    '<a href="forgot">request a new password</a> again')
            self.addPortalStatusMessage(msg)
            return self.redirect("%s/login" % self.siteURL)

        # Automatically log the user in
        self.login(userid)
        
        self.addPortalStatusMessage(u'Your password has been reset and you '
                                    'are now logged in.')
        self.redirect('%s/account' % self.memfolder_url(userid))
        return True

    @property
    def key(self):
        key = self.request.get('key')
        pw_tool = self.get_tool("portal_password_reset")
        try:
            pw_tool.verifyKey(key)
        except "InvalidRequestError": # XXX rollie? # string exceptions?
            raise Forbidden, "You fool! The Internet Police have already been notified of this incident. Your IP has been confiscated."
        except "ExpiredRequestError": # XXX rollie?
            raise Forbidden, "YOUR KEY HAS EXPIRED. Please try again"
        return key

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
        
        if email:
            self._sendmail_to_pendinguser(member.getId(),
                                          email,
                                          self._confirmation_url(member))
            mfrom = self.portal.getProperty('email_from_address')
            msg = 'A new email has been sent to %s from %s, make sure you follow the link in the email to activate your account' % (email, mfrom)

        self.addPortalStatusMessage(msg)

    def handle_request(self):
        self._pending_member()

def email_confirmation():
    """get email confirmation mode from zope.conf"""
    cfg = config.getConfiguration().product_config.get('opencore.nui')
    if cfg:
        val = cfg.get('email-confirmation', 'True').title()
        if val == 'True':
            return True
        elif val == 'False':
            return False
        else:
            raise ValueError('email-confirmation should be "True" or "False"')
    return True # the default
