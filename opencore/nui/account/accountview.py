"""
views pertaining to accounts -- creation, login, password reset
"""
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.interfaces.membership import IEmailInvites
from opencore.member.interfaces import IHandleMemberWorkflow
from opencore.nui.account.utils import email_confirmation
from opencore.nui.base import BaseView, _
from opencore.nui.email_sender import EmailSender
from opencore.nui.formhandler import * # start import are for pansies
from opencore.siteui.member import FirstLoginEvent
from plone.memoize import instance
from smtplib import SMTPRecipientsRefused, SMTP
from zExceptions import Forbidden, Redirect, Unauthorized
from zope.component import getUtility
from zope.event import notify
import logging
import urllib


logger = logging.getLogger("opencore.nui.accountview")

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
        self.request.set('__ac_name', member_id)
        self.auth.login()
        # Note that login() doesn't actually seem to log us in during
        # the current request.  eg. this next line:
        self.membertool.setLoginTimes() # XXX does nothing, we're anonymous.

    def update_credentials(self, member_id):
        return self.auth.updateCredentials(self.request, self.response,
                                           member_id, None)
    
    @property
    def login_url(self):
        return "%s/login" % self.context.absolute_url()

    def logged_in_user_js(self):
        """Get info about the current member (if any), as javascript.
        (We use a callback so client knows when this script has loaded.)
        """
        info = self.member_info
        if info:
            return """
            OpenCore.prepareform({
            loggedin: true,
            id: '%(id)s',
            name: '%(fullname)s',
            profileurl: '%(url)s/profile',
            memberurl: '%(url)s',
            website: '%(website)s',
            email: '%(email)s'
            });
            """ % info
        else:
            # Not logged in.
            return """
            OpenCore.prepareform({
            loggedin: false
            });
            """

    ### methods to deal with pending members

    def is_pending(self, **query):
        matches = self.membranetool.unrestrictedSearchResults(**query)
        if len(matches) != 1:
            return
        member = matches[0].getObject()
        if IHandleMemberWorkflow(member).is_unconfirmed():
            return member

    def _confirmation_url(self, mem):
        code = mem.getUserConfirmationCode()
        return "%s/confirm-account?key=%s" % (self.siteURL, code)

    def _sendmail_to_pendinguser(self, user_name, email, url):
        """ send a mail to a pending user """
        # TODO only send mail if in the pending workflow state

        message = _(u'email_to_pending_user',
                    mapping={u'user_name':user_name,
                             u'url':url,
                             u'portal_url':self.siteURL,
                             u'portal_title':self.portal_title()})
        
        sender = EmailSender(self, secureSend=True)
        subject = _(u'email_to_pending_user_subject',
                    u'Welcome to ${portal_title}! - Please confirm your email address',
                    mapping={u'portal_title':self.portal_title()})

        sender.sendEmail(mto=email,
                         msg=message,
                         subject=subject)


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
            self.addPortalStatusMessage(_(u'psm_account_not_activated',u"""Your account has not yet been activated. An email was sent to ${user} from ${email_from_address} containing a link to activate your account.""",
                                          mapping={u'user':member.getEmail(), u'email_from_address':self.portal.getProperty('email_from_address')}))
            self.redirect('pending?key=%s' % member.UID())
            return True
        return False

    @button('login')
    @post_only(raise_=False)
    def handle_login(self):
        if self.login_pending_member(): return

        id_ = self.request.get('__ac_name')
        if self.loggedin:
            self.addPortalStatusMessage(_(u'psm_signin_welcome', u'Welcome! You have signed in.'))
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

        self.addPortalStatusMessage(_(u'psm_check_username_password', u'Please check your username and password. If you still have trouble, you can <a href="forgot">retrieve your sign in information</a>.'))

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
            return default_redirect  # need to restrict domain!
            referer = self.request.get('http_referer')
            if not referer or referer in self.boring_urls:
                return default_redirect
            anchor = self.request.get('came_from_anchor')
            if anchor:
                referer = '%s#%s' % (referer, anchor)
            return referer

    def logout(self, redirect=None):
        logout = self.cookie_logout

        self.invalidate_session()
            
        self.add_status_message(_(u'psm_signed_out', u"You have signed out."))
        
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
        self.add_status_message(_(u'psm_not_sufficient_perms', u"You do not have sufficient permissions."))
        if not self.loggedin:
            self.redirect(self.login_url)
            

    
class ConfirmAccountView(AccountView):

    @property
    def key(self):
        return self.request.form["key"]
    
    @instance.memoizedproperty
    def member(self):
        member = None
        
        try:
            UID, confirmation_key = self.key.split('confirm')
        except KeyError:
            return None
        except ValueError: # if there is no 'confirm' (or too many?)
            return None
    
        # we need to do an unrestrictedSearch because a default search
        # will filter results by user permissions
        matches = self.membranetool.unrestrictedSearchResults(UID=UID)
        if matches:
            member = matches[0].getObject()
        if member._confirmation_key != confirmation_key:
            return None

        return member

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


class InitialLogin(BaseView):

    def first_login(self):
        member = self.membertool.getAuthenticatedMember()
        if not self.loggedin:
            # Pretty much everything else in this method will fail.
            logger.warn("Anonymous got into first_login, should never happen!")
            raise Unauthorized("You must log in.")
        if not self.membertool.getHomeFolder():
            self.membertool.createMemberArea(member.getId())

        # set login time since for some reason zope doesn't do it
        
        member.setLogin_time(DateTime())

        # first check for any pending requests which are also email invites
        from zope.component import getMultiAdapter
        from opencore.interfaces import IPendingRequests
        from opencore.interfaces.pending_requests import IRequestMembership
        mship_bucket = getMultiAdapter((member, self.portal.projects), IPendingRequests)
        email_invites_bucket = getUtility(IEmailInvites)

        email_invites = email_invites_bucket.getInvitesByEmailAddress(member.getEmail()).keys()
        pending_requests = mship_bucket.getRequests().keys()
        mships_to_confirm = [mship for mship in email_invites if mship in pending_requests]
        
        # convert email invites into mship objects
        email_invites = email_invites_bucket.convertInvitesForMember(member)
        
        # autoconfirm any mships which both the admin and the user already took action on
        for mship in email_invites:
            # copied from join.py, should combine
            mship._v_self_approved = True
            proj_id = mship.aq_parent.getId()
            if proj_id in mships_to_confirm:
                mship.do_transition('approve_public')
                mship_bucket.removeRequest(proj_id)
                
        # convert pending mship requests into real mship requests
        converted = mship_bucket.convertRequests()
        for proj_title in converted:
            self.add_status_message(_(u'team_proj_join_request_sent',
                                      u'Your request to join "${project_title}" has been sent to the project administrator(s).',
                                      mapping={'project_title':proj_title}))

        baseurl = self.memfolder_url()
        # Go to the user's Profile Page in Edit Mode
        return self.redirect("%s/%s" % (self.memfolder_url(),
                                        'tour'))


class ForgotLoginView(AccountView):

    # XXX this class should store some sort of member data
    # on a per request basis.  as it is now, multiple
    # catatlogue queries are done for the same user
    # which can't be good

    @anon_only(BaseView.siteURL)
    @button('send')
    @post_only(raise_=False)
    def handle_request(self):
        userid = self.userid
        if userid:

            if self.is_pending(getUserName=userid):
                self.redirect('%s/resend-confirmation?member=%s' % (self.siteURL, userid))
                return
            
            if email_confirmation():
                self._mailPassword(userid)
                self.addPortalStatusMessage(_(u'psm_forgot_login',
                                              u'Your username is ${user_id}.  If you would like to reset your password, please check your email account for further instructions.',
                                              mapping={u'user_id': userid}))
            else:
                self.redirect(self.reset_url)
            return True

        # else the user isn't found
        self.addPortalStatusMessage(u"We can't find your account.")

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
            mail_text = _(u'email_forgot_password', u'You requested a password reminder for your ${portal_title} account. If you did not request this information, please ignore this message.\n\nTo change your password, please visit the following URL: ${url}',
                          mapping={u'url':self.reset_url})
            sender = EmailSender(self, secureSend=True)
            sender.sendEmail(mto=email, 
                        msg=mail_text,
                        subject=_(u'email_forgot_password_subject', u'%s - Password reminder' % self.portal_title()))
        except SMTPRecipientsRefused:
            # Don't disclose email address on failure
            # XXX is this needed?
            raise SMTPRecipientsRefused('Recipient address rejected by server')

    @property
    def userid(self):
        user_lookup = self.request.get("__ac_name")
        if not user_lookup:
            self.addPortalStatusMessage(_(u'psm_enter_username_email', u"Please enter your username or email address."))
            return None

        query = dict()
        if '@' in user_lookup:
            query['getEmail'] = user_lookup
        else:
            query['getUserName'] = user_lookup

        brains = self.membranetool.unrestrictedSearchResults(query)
        if brains:
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
            msg = _(u'psm_pass_reset_fail', u'Password reset attempt failed. Did you mistype your username or password?')
            self.addPortalStatusMessage(msg)
            return self.redirect(self.siteURL)
        except 'ExpiredRequestError':
            msg = _(u'psm_pass_reset_expired', u'Your password reset request has expired. '
                    'You can <a href="login">sign in</a> again using '
                    'your old username and password or '
                    '<a href="forgot">request a new password</a> again.')
            self.addPortalStatusMessage(msg)
            return self.redirect("%s/login" % self.siteURL)

        # Automatically log the user in
        self.login(userid)
        
        self.addPortalStatusMessage(_(u'psm_password_reset', u'Welcome! Your password has been reset, and you are now signed in.'))
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
            raise Forbidden, "Your password reset key Please try again."
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
        
        mem_name = member.getFullname()
        mem_name = mem_name or mem_id

        if email:
            self._sendmail_to_pendinguser(mem_name,
                                          email,
                                          self._confirmation_url(member))
            mfrom = self.portal.getProperty('email_from_address')
            msg = _(u'psm_new_activation', u'A new activation email has been sent to ${email} from ${mfrom}. <br />Please follow the link in the email to activate this account.',
                    mapping={u'email':email, u'mfrom':mfrom})

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
        mem_name = mem_name or mem_id
        self._sendmail_to_pendinguser(mem_name,
                                      member.getEmail(),
                                      self._confirmation_url(member))
        self.add_status_message('A new activation email has been sent to the email address provided for %s.' % name)
        self.redirect("%s/login" %self.siteURL)



