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
from opencore.nui.email_sender import EmailSender
from opencore.nui.formhandler import *
from DateTime import DateTime

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
        # TODO only send mail if in the pending workflow state
        mailhost_tool = self.get_tool("MailHost")

        # TODO move this to a template for easier editting
        message = """You recently signed up to use OpenPlans.org. 

Please confirm your email address at the following address: %s

If you cannot click on the link, you can cut and paste it into your browser's address bar.

Once you have confirmed, you can start using OpenPlans.

If you did not initiate this request or believe it was sent in error you can safely ignore this message.

Cheers,
The OpenPlans Team
www.openplans.org""" % url
        
        sender = EmailSender(self, secureSend=True)
        sender.sendEmail(mto=email,
                         msg=message,
                         subject='Welcome to OpenPlans! - Confirm your email')


class LoginView(AccountView):

    @property
    def boring_urls(self):
        """
        a list of urls which should not be redirected
        back to after login because they are boring.
        """
        urls = [self.siteURL,]
        more_urls = [self.url_for(x) for x in ("login", "forgot", "join")]
        urls += more_urls
        return urls

    def login_pending_member(self):
        # check to see if the member is pending
        member = None
        id_ = self.request.get('__ac_name')
        password = self.request.form.get('__ac_password')
        if id_ and password:
            member = self.is_pending(getUserName=id_)

        # ensure there is one match and the password is right
        if member and member.verifyCredentials({'login': id_, 
                                                'password': password}):
            self.addPortalStatusMessage("""Your account has not yet been activated. An email was sent to %s from %s containing a link to activate your account.""" %
                (member.getEmail(),
                 self.portal.getProperty('email_from_address')))
            self.redirect('pending?key=%s' % member.UID())
            return True
        return False

    @button('login')
    @post_only(raise_=False)
    def handle_login(self):
        if self.login_pending_member(): return

        id_ = self.request.get('__ac_name')
        if self.loggedin:
            self.addPortalStatusMessage('Welcome! You have signed in.')
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

        self.addPortalStatusMessage(u'Please check your username and password. If you still have trouble, you can <a href="forgot">retrieve your sign in information</a>.')

    @anon_only(BaseView.siteURL)
    def handle_request(self):
        """ redirect logged in users """
        
    @property
    def came_from(self):
        return self.request.get('came_from', '')

    @property
    def destination(self):
        """where you go after you're logged in"""
        if self.came_from: # (if insufficient privileges)
            destination = self.came_from 

            # append referer to destination as query string 
            # in order for insufficient_privileges to redirect correctly
            referer = self.request.form.get('referer')
            if referer is not None:
                destination = '%s?referer=%s' % (destination, 
                                                 urllib.quote(referer))
            return destination
        else:
            default_redirect = '%s/account' % self.memfolder_url()
            referer = self.request.get('http_referer')
            if not referer or referer in self.boring_urls:
                return default_redirect
            return referer

    def logout(self, redirect=None):
        logout = self.cookie_logout

        self.invalidate_session()
            
        self.add_status_message("You have signed out.")
        
        if redirect is None:
            redirect = self.login_url
            
        self.redirect("%s" %redirect)

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
        self.add_status_message("You do not have sufficient permissions.")
        if not self.loggedin:
            self.redirect(self.login_url)
            

class JoinView(AccountView, OctopoLite):

    template = ZopeTwoPageTemplateFile('join.pt')

    @anon_only(BaseView.siteURL)
    def handle_request(self):
        """ redirect logged in users """

    @action('join', apply=post_only(raise_=False))
    def create_member(self, targets=None, fields=None):
        mdc = self.get_tool('portal_memberdata')
        mem = mdc._validation_member

        self.errors = {}
        
        self.errors = mem.validate(REQUEST=self.request,
                                   errors=self.errors,
                                   data=1, metadata=0)
        password = self.request.form.get('password')
        password2 = self.request.form.get('confirm_password')
        if not password and not password2:
            self.errors.update({'password': 'Please enter a password' })

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
            self.addPortalStatusMessage(u'Thanks for joining OpenPlans, %s!\nA confirmation email has been sent to you with instructions on activating your account.' % mem_id)
            self.redirect(self.portal_url())
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
            ret['oc-%s-error' % e] = {
                'html': str(errors[e]),
                'action': 'copy', 'effects': 'highlight'}
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
            self.addPortalStatusMessage(u'You have tried to activate an account that is not pending confirmation. Please sign in normally.')
            return False
        
        # need to set/delete the attribute for the workflow guards
        setattr(member, 'isConfirmable', True)
        pf.doActionFor(member, 'register_public')
        delattr(member, 'isConfirmable')
        return True
        
    def handle_confirmation(self, *args, **kw):
        member = self.member
        if not member:
            self.addPortalStatusMessage(u'Denied -- bad key')
            return self.redirect("%s/%s" %(self.siteURL, 'login'))
        
        # redirect to login page if confirmation isn't pending
        if not self.confirm(member):
            return self.redirect("%s/login" %self.siteURL)
        
        self.login(member.getId())
        return self.redirect("%s/init-login" %self.siteURL)


class InitialLogin(BaseView):

    def first_login(self):
        member = self.membertool.getAuthenticatedMember()
        if not self.membertool.getHomeFolder():
            self.membertool.createMemberArea(member.getId())

        # set login time since for some reason zope doesn't do it
        member.setLogin_time(DateTime())

        baseurl = self.memfolder_url()
        # Go to the user's Profile Page in Edit Mode
        return self.redirect("%s/%s" % (self.memfolder_url(),
                                        'profile-edit?first_login=1'))


class ForgotLoginView(AccountView):

    @anon_only(BaseView.siteURL)
    @button('send')
    @post_only(raise_=False)
    def handle_request(self):
        userid = self.userid
        if userid:
            if email_confirmation():
                self._mailPassword(userid)
                self.addPortalStatusMessage('Your username is %s.  If you would like to reset your password, please check your email account for further instructions.' % userid)
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
            raise Unauthorized, "Mailing forgotten passwords has been disabled."

        member = self.membranetool(getId=forgotten_userid)

        if member is None:
            raise ValueError, 'The username you entered could not be found.'
        
        member = member[0].getObject()        
        email = member.getEmail()

        try:
            pwt = self.get_tool("portal_password_reset")
            mail_text = self.render_static("account_forgot_password_email.txt")
            mail_text += self.reset_url
            sender = EmailSender(self, secureSend=True)
            sender.sendEmail(mto=email, 
                        msg=mail_text,
                        subject='OpenPlans - Password reminder')
        except SMTPRecipientsRefused:
            # Don't disclose email address on failure
            # XXX is this needed?
            raise SMTPRecipientsRefused('Recipient address rejected by server')

    @property
    def userid(self):
        user_lookup = self.request.get("__ac_name")
        if not user_lookup:
            self.addPortalStatusMessage(u"Please enter your username or email address.")
            return None
        
        if '@' in user_lookup:
            brains = self.membranetool(getEmail=user_lookup)
        else:
            brains = self.membranetool(getUserName=user_lookup)

        if not brains:
            self.addPortalStatusMessage(u"We can't find your account. This could be because you have not yet completed your email confirmation.")
            return
        return brains[0].getId


class PasswordResetView(AccountView):
    
    @button('set')
    @post_only(raise_=False)
    def handle_reset(self):
        password = self.request.form.get("password")
        password2 = self.request.form.get("password2")
        userid = self.request.form.get("userid")
        randomstring = self.request.form.get("key")

        # validate the password input
        member = self.validate_password_form(password, password2, userid)
        if not member:
            return False
        userid = member.getId()

        pw_tool = self.get_tool("portal_password_reset")
        try:
            pw_tool.resetPassword(userid, randomstring, password)
        except 'InvalidRequestError':
            # XXX TODO redirect to 404 instead
            msg = u'Password reset attempt failed. Did you mistype your username or password?'
            self.addPortalStatusMessage(msg)
            return self.redirect(self.siteURL)
        except 'ExpiredRequestError':
            msg = u'Your password reset request has expired.'
            msg += (u'You can <a href="login">sign in</a> again using'
                    'your old username and password or '
                    '<a href="forgot">request a new password</a> again.')
            self.addPortalStatusMessage(msg)
            return self.redirect("%s/login" % self.siteURL)

        # Automatically log the user in
        self.login(userid)
        
        self.addPortalStatusMessage(u'Welcome! Your password has been reset, and you are now signed in.')
        self.redirect('%s/account' % self.memfolder_url(userid))
        return True

    @property
    def key(self):
        key = self.request.get('key')
        pw_tool = self.get_tool("portal_password_reset")
        try:
            pw_tool.verifyKey(key)
        except "InvalidRequestError":
            raise Forbidden, "Your password reset key is invalid. Please verify that it is identical to the email and try again."
        except "ExpiredRequestError":
            raise Forbidden, "Your password reset key has expired. Please try again."
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
            msg = 'A new activation email has been sent to %s from %s. Please follow the link in the email to activate this account.' % (email, mfrom)

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
