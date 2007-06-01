"""
views pertaining to accounts -- creation, login, password reset
"""
from smtplib import SMTPRecipientsRefused

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.remember.utils import getAdderUtility
from plone.memoize import instance
from opencore.nui.base import BaseView, button, post_only, anon_only
from zExceptions import Forbidden, Redirect
from Globals import DevelopmentMode as DEVMODE

class JoinView(BaseView):

    @button('join')
    @post_only(raise_=False)
    def handle_request(self):
        context = self.context
        mdc = getToolByName(context, 'portal_memberdata')

        adder = getAdderUtility(context)
        type_name = adder.default_member_type

        #00 pythonscript call, move to fs code
        id_ = context.generateUniqueId(type_name)
        mem = mdc.restrictedTraverse('portal_factory/%s/%s' % (type_name, id_))
        self.txn_note('Initiated creation of %s with id %s in %s' % \
                             (mem.getTypeInfo().getId(),
                              id_,
                              context.absolute_url()))
        self.errors = {}
        self.errors = mem.validate(REQUEST=self.request,
                                   errors=self.errors,
                                   data=1, metadata=0)

        if self.errors:
            return self.errors

        mem_id = self.request.get('id')
        mem = mdc.portal_factory.doCreate(mem, mem_id)
        result = mem.processForm()
        url = self.confirmation_url(mem)
        
        if DEVMODE:
            return dict(confirmation=url, devmode=True, member_id=mem_id)
        else:
            self._sendMailToPendingUser(id=mem_id,
                                        email=self.request.get('email'),
                                        url=url)
            return mdc._getOb(mem_id)

    def confirmation_url(self, mem):
        code = mem.getUserConfirmationCode()
        return "%s/confirm-account?key=%s" % (self.siteURL, code)
    
    def _sendMailToPendingUser(self, id, email, url):
        """ send a mail to a pending user """
        ## XX todo only send mail if in the pending workflow state
        mailhost_tool = getToolByName(self.context, "MailHost")

        mfrom = self.portal.getProperty('email_from_address')
        
        mailhost_tool.send("how are you %s?\ngo here: %s" % (id, url),
                           mto=email,
                           mfrom=mfrom,
                           subject='OpenPlans account registration')
        

class ConfirmAccountView(BaseView):

    def __call__(self, *args, **kw):
        key = self.request.get("key")
        
        # we need to do an unrestrictedSearch because a default search
        # will filter results by user permissions
        matches = self.membranetool.unrestrictedSearchResults(UID=key)
        if not matches:
            self.addPortalStatusMessage(u'Denied -- bad key')
            return self.redirect(self.siteURL + '/login')

        assert len(matches) == 1
        
        member = matches[0].getObject()
        
        # Move member into the confirmed workflow state
        pf = getToolByName(self, "portal_workflow")
        if pf.getInfoFor(member, 'review_state') != 'pending':
            self.addPortalStatusMessage(u'Denied -- no confirmation pending')
            return self.redirect(self.siteURL + '/login')
        
        setattr(member, 'isConfirmable', True)
        pf.doActionFor(member, 'register_public')
        delattr(member, 'isConfirmable')

        # Automatically log the user in
        auth = getToolByName(getToolByName(self.portal, "acl_users"),
                             "credentials_signed_cookie_auth")
        auth.updateCredentials(self.request, self.request.response,
                               member.id, None)

        # Go to the user's Profile Page in Edit Mode
        self.addPortalStatusMessage(u'Welcome!')
        self.addPortalStatusMessage(u'first time!')

        return self.redirect(self.siteURL + '/logged_in')


class ForgotLoginView(BaseView):

    @button('send')
    @post_only(raise_=False)
    def handle_request(self):
        if self.userid:
            if DEVMODE:
                return dict(devmode=True,
                            reset_url=self.reset_url,
                            userid = self.userid)
            else:
                self._mailPassword(self.userid)
            return True
        return False
    
    @instance.memoizedproperty
    def randomstring(self):
        pwt = self.get_tool("portal_password_reset")
        obj = pwt.requestReset(self.userid)
        return obj['randomstring']

    @property
    def reset_url(self):
        return '\n%s/reset-password?key=%s' % (self.siteURL, self.randomstring)
    
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


class PasswordResetView(BaseView):
    
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
        auth = self.get_tool("acl_users").credentials_signed_cookie_auth
        auth.updateCredentials(self.request, self.request.response,
                               userid, None)
        
        self.addPortalStatusMessage(u'Your password has been reset and you are now logged in.')
        self.redirect(self.siteURL)
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


