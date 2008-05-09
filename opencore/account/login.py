"""
login views
"""
import logging
from Products.CMFCore.utils import getToolByName
from opencore.account.browser import AccountView
from opencore.account.utils import email_confirmation
from opencore.browser.base import BaseView, _
from opencore.browser.formhandler import button, post_only, anon_only
from opencore.interfaces import IPendingRequests
from opencore.interfaces.event import FirstLoginEvent
from opencore.interfaces.membership import IEmailInvites
from opencore.interfaces.pending_requests import IRequestMembership
from opencore.configuration.utils import get_config
from opencore.nui.email_sender import EmailSender
from plone.memoize import instance
from smtplib import SMTPRecipientsRefused
from topp.utils.uri import uri_same_source
import urllib
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.event import notify
from zExceptions import Redirect, Unauthorized
from DateTime import DateTime

logger = logging.getLogger("opencore.account.login")

class LoginView(AccountView):

    @property
    def boring_urls(self):
        """
        a list of urls which should not be redirected
        back to after login because they are boring.
        """
        site_url = getToolByName(self.context, 'portal_url')()
        urls = [site_url,]
        #XXX this should be configuration
        more_urls = ['%s/%s' % (site_url, screen)
                     for screen in ("login", "forgot", "join", "message")]
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
            # @@ move out of skins!!!
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

    @anon_only(lambda view: view.context.portal_url())
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
                if '?' in destination:
                    destination = '%s&referer=%s' % (destination, 
                                                     urllib.quote(referer))
                else:
                    destination = '%s?referer=%s' % (destination, 
                                                     urllib.quote(referer))
            return destination
        else:
            default_redirect = '%s/account' % self.memfolder_url()
            referer = self.request.get('http_referer')
            if not self.should_redirect_back(referer):
                return default_redirect
            anchor = self.request.get('came_from_anchor')
            if anchor:
                referer = '%s#%s' % (referer, anchor)
            return referer

    def should_redirect_back(self, url):
        # We need a valid url in order to perform further tests
        if not url:
            return False
        if url.startswith(getToolByName(self.context, 'portal_url')()) and \
               url not in self.boring_urls:
            return True
        raw_list = get_config('applications', 'opencore_vacuum_whitelist', default='').split(',')
        vacuum_whitelist = [x.strip() for x in raw_list if x.strip()]
        
        for safe_host in vacuum_whitelist:
            if uri_same_source(url, safe_host):
                return True
        return False

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
        try:
            sdm = self.get_tool('session_data_manager')
        except AttributeError:
            return

        session = sdm.getSessionData(create=0)
        if session is not None:
            session.invalidate()

    def privs_redirect(self):
        self.add_status_message(_(u'psm_not_sufficient_perms', u"You do not have sufficient permissions."))
        if not self.loggedin:
            self.redirect(self.login_url)


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
                                      u'Your request to join "${project_title}" has been sent to the ${project_noun} administrator(s).',
                                      mapping={'project_title':proj_title,
                                               'project_noun':self.project_noun}))

        baseurl = self.memfolder_url()
        # Go to the user's Profile Page in Edit Mode
        default_redirect = "%s/%s" % (self.memfolder_url(), 'tour')
        redirect_url = self.request.form.get('go_to', default_redirect)
        return self.redirect(redirect_url)

class ForgotLoginView(AccountView):

    # XXX this class should store some sort of member data
    # on a per request basis.  as it is now, multiple
    # catatlogue queries are done for the same user
    # which can't be good

    @anon_only(lambda view: view.context.portal_url())
    @button('send')
    @post_only(raise_=False)
    def handle_request(self):
        site_url = getToolByName(self.context, 'portal_url')()
        userid = self.userid
        if userid:

            if self.is_pending(getUserName=userid):
                self.redirect('%s/resend-confirmation?member=%s' % (site_url, userid))
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
        site_url = getToolByName(self.context, 'portal_url')()
        return '%s/reset-password?key=%s' % (site_url, self.randomstring)
    
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
            mail_text = _(u'email_forgot_password', u'You requested a password reset for your ${portal_title} account. If you did not request this information, please ignore this message.\n\nTo change your password, please visit the following URL: ${url}',
                          mapping={u'url':self.reset_url})
            sender = EmailSender(self, secureSend=True)
            sender.sendEmail(mto=email, 
                        msg=mail_text,
                        subject=_(u'email_forgot_password_subject', u'${portal_title} - Password reset', mapping={u'portal_title':self.portal_title()}))
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
