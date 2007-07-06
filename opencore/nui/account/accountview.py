"""
views pertaining to accounts -- creation, login, password reset
"""
from AccessControl.SecurityManagement import newSecurityManager
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.remember.utils import getAdderUtility
from opencore.nui.base import BaseView
from opencore.nui.formhandler import *
from opencore.siteui.member import notifyFirstLogin
from plone.memoize import instance
from smtplib import SMTPRecipientsRefused, SMTP
from zExceptions import Forbidden, Redirect, Unauthorized
from App import config
import urllib
import socket
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class AccountView(BaseView):
    """
    base class for views dealing with accounts
    distinguised by its login functionality
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
    def home_page(self):
        """
        returns the 'home page' of the user.
        this is somewhat hacky.  maybe the urls will fix themselves
        """
        return '%s/profile' % self.home_url

class LoginView(AccountView):

    @button('login')
    @post_only(raise_=False)
    def handle_login(self):
        if self.loggedin:
            self.addPortalStatusMessage('You are logged in')
            id_ = self.request.get('__ac_name')
            self.update_credentials(id_)
            self.membertool.setLoginTimes()
            self.membertool.createMemberArea()

            destination = self.destination
            referer = self.request.form.get('referer')
            if referer is not None:
                destination = '%s?referer=%s' % (destination, 
                                                 urllib.quote(referer))
            return self.redirect(destination)

        self.addPortalStatusMessage('Login failed')

    @anon_only(AccountView.home_page)
    def handle_request(self):
        pass
            
    @property
    def referer(self):
        return self.request.get('came_from', '')

    def already_loggedin(self):
        if self.loggedin and self.request.get('loggedout'):
            return self.http_root_logout
        if self.loggedin:
            return True

    @property
    def destination(self):
        """where you go after you're logged in"""
        retval = self.referer
        if not retval:
            if self.home_url:
                retval = self.home_page
            else:
                retval = self.siteURL
        return retval

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
            

def ugly_hack(func):
    def inner(self):
        ret = func(self)
        return self.render()
    return inner

class JoinView(BaseView, OctopoLite):

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
            self.addPortalStatusMessage(u'An email has been sent to you, Lammy.')
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
        # Go to the user's Profile Page in Edit Mode
        return self.redirect("%s/%s" % (self.home_url_for_id(member.getId()),
                                        'profile-edit'))


class ForgotLoginView(AccountView):

    @anon_only(AccountView.home_page)
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
            self.addPortalStatusMessage(u"User id or email not found")
            return None
        return brains[0].getId


class PasswordResetView(AccountView):
    
    @button('set')
    @post_only(raise_=False)
    def handle_reset(self):
        password = self.request.get("password")
        password2 = self.request.get("password2")
        if not password or not password2:
            self.addPortalStatusMessage("you must enter a password.")
            return False
        if password != password2:
            self.addPortalStatusMessage("passwords don't match")
            return False

        userid = self.request.get("userid")
        randomstring = self.request.get("key")

        pw_tool = self.get_tool("portal_password_reset")
        try:
            pw_tool.resetPassword(userid, randomstring, password)
        except 'InvalidRequestError':
            self.addPortalStatusMessage(u'Cannot reset password of "%s"' %
                                        userid)
            return False
        except 'ExpiredRequestError':
            self.addPortalStatusMessage(u'The password reset request for %s has expired' %
                                        userid)
            return False

        # Automatically log the user in
        self.login(userid)
        
        self.addPortalStatusMessage(u'Your password has been reset and you are now logged in.')
        self.redirect('%s/preferences' % self.home_url_for_id(userid))
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
