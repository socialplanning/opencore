"""
views pertaining to accounts -- creation, login, password reset
"""
from AccessControl.SecurityManagement import newSecurityManager
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.remember.utils import getAdderUtility
from opencore.nui.base import BaseView, button, post_only, anon_only
from opencore.siteui.member import notifyFirstLogin
from plone.memoize import instance
from smtplib import SMTPRecipientsRefused, SMTP
from zExceptions import Forbidden, Redirect
from App import config
import socket

# get email confirmation mode from zope.conf

email_confirmation = True
cfg = config.getConfiguration().product_config.get('opencore.nui')
if cfg:
    email_confirmation = eval(cfg.get('email-confirmation', 'True'))

# alternatively, see if you can use sendmail
# this could also be used in conjunction with the zope.conf variable
#email_confirmation = True
#try:
#    SMTP('localhost')
#except socket.error:
#    email_confirmation = False

class AccountView(BaseView):
    """
    base class for views dealing with accounts
    distinguised by its login functionality
    """

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
        return

    def update_credentials(self, member_id):
        return self.auth.updateCredentials(self.request, self.response,
                                           member_id, None)


class LoginView(AccountView):

    @property
    def referer(self):
        return self.request.get('came_from', '')

    @property
    def destination(self):
        """where you go after you're logged in"""
        retval = self.referer
        if not retval:
            retval = '/'.join((self.home(), 'profile'))
        return retval

    @button('login')
    @post_only(raise_=False)
    def handle_login(self):
        if self.loggedin:
            self.addPortalStatusMessage('You are logged in')
            self.update_credentials(self.loggedinmember.getId())
            return self.redirect(self.destination)

        self.addPortalStatusMessage('Login failed')
            
        if self.referer:
            self.addPortalStatusMessage('Hey! you came from %s' %self.referer)


class JoinView(BaseView):

    @button('join')
    @post_only(raise_=False)
    def handle_request(self):
        context = self.context
        mdc = getToolByName(context, 'portal_memberdata')
        adder = getAdderUtility(context)
        type_name = adder.default_member_type

        temp_mem_id = self.temp_mem_id
        mem = mdc.portal_factory.restrictedTraverse("%s/%s" % (type_name, temp_mem_id))

        self.errors = {}
        self.errors = mem.validate(REQUEST=self.request,
                                   errors=self.errors,
                                   data=1, metadata=0)

        if self.errors:
            return self.errors

        mem_id = self.request.get('id')
        mem = mdc.portal_factory.doCreate(mem, mem_id)
        self.txn_note('Created %s with id %s in %s' % \
                      (mem.getTypeInfo().getId(),
                       mem_id,
                       self.context.absolute_url()))
        result = mem.processForm()
        url = self._confirmation_url(mem)

        if email_confirmation:
            self._sendmail_to_pendinguser(id=mem_id,
                                        email=self.request.get('email'),
                                        url=url)
            return mdc._getOb(mem_id)
        else:
            return self.redirect(url)

    @instance.memoizedproperty
    def temp_mem_id(self):
        # only want to create one dummy
        id_ = self.request.get('temp_mem_id')
        if id_:
            return id_

        mdc = self.get_tool('portal_memberdata')
        adder = getAdderUtility(self.context)
        type_name = adder.default_member_type

        #00 pythonscript call, move to fs code
        id_ = self.context.generateUniqueId(type_name)
        mem = mdc.restrictedTraverse('portal_factory/%s/%s' % (type_name, id_))

        return id_

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
        key = self.request.get("key")
        assert key
        return key
    
    @instance.memoizedproperty
    def member(self):
        member = None
        
        # we need to do an unrestrictedSearch because a default search
        # will filter results by user permissions
        matches = self.membranetool.unrestrictedSearchResults(UID=self.key)
        if len(matches):
            member = matches[0].getObject()
        return member

    def confirm(self, member):
        """Move member into the confirmed workflow state"""
        pf = self.get_tool("portal_workflow")
        if pf.getInfoFor(member, 'review_state') != 'pending':
            self.addPortalStatusMessage(u'Denied -- no confirmation pending')

            # use string interpolation pls
            return self.redirect(self.siteURL + '/login')
        
        setattr(member, 'isConfirmable', True)
        pf.doActionFor(member, 'register_public')
        delattr(member, 'isConfirmable')
        
    def __call__(self, *args, **kw):
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

        folder=self.membertool.getHomeFolder(member.getId())
        
        # Go to the user's Profile Page in Edit Mode
        self.addPortalStatusMessage(u'Welcome to OpenPlans!')
        return self.redirect("%s/%s" %(folder.absolute_url(), 'profile-edit'))


class ForgotLoginView(BaseView):

    @button('send')
    @post_only(raise_=False)
    def handle_request(self):
        if self.userid:
            if email_confirmation:
                self._mailPassword(self.userid)
            else:
                return self.redirect(self.reset_url)
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
        
        if user_lookup.find('@') >= 0:
            brains = self.membranetool(getEmail=user_lookup)
        else:
            brains = self.membranetool(getId=user_lookup)

        if not len(brains):
            self.addPortalStatusMessage(u"User id or email not found")
            return None
        return brains[0].getId


class PasswordResetView(AccountView):
    
    @button('set')
    @post_only(raise_=False)
    def handle_reset(self):
        password = self.request.get("password")
        if not password:
            self.addPortalStatusMessage("you must enter a password.")
            return False
        
        userid = self.request.get("userid")
        randomstring = self.request.get("key")
        pw_tool = self.get_tool("portal_password_reset")
        pw_tool.resetPassword(userid, randomstring, password)

        # Automatically log the user in
        self.login(userid)
        
        self.addPortalStatusMessage(u'Your password has been reset and you are now logged in.')
        self.redirect(self.home(userid) + '/profile')
        return True

    @property
    def key(self):
        key = self.request.get('key')
        pw_tool = self.get_tool("portal_password_reset")
        try:
            pw_tool.verifyKey(key)
        except "InvalidRequestError": # XXX rollie?
            raise Forbidden, "You fool! The Internet Police have already been notified of this incident. Your IP has been confiscated."
        except "ExpiredRequestError": # XXX rollie?
            raise Forbidden, "YOUR KEY HAS EXPIRED. Please try again"
        return key


class HomeView(BaseView):
    """redirects a user to their home"""
    # XXX this doesn't work since __call__ has been switched to redirect.  

    def joinurls(self, *args):
        """This function is because urlparse.urljoin doesn't behave nice"""
        # XXX probably this should be eliminated or moved
        return '/'.join([ i.strip('/') for i in args ])

    def redirect(self):
        home = self.home()
        url = self.siteURL
        if home:            
            if self.request.get('profile-edit') is not None:                
                url = self.joinurls(home, 'profile-edit')
        raise Redirect, url


