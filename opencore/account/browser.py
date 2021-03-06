from opencore.browser.base import BaseView
from opencore.i18n import _
from opencore.member.interfaces import IHandleMemberWorkflow
from opencore.utility.interfaces import IEmailSender
from opencore.nui.email_sender import EmailSender
from AccessControl.SecurityManagement import newSecurityManager
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName

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
        uf = getToolByName(self.context, "acl_users")
        return uf.credentials_signed_cookie_auth
    
    def login(self, member_id):
        """login a user programmatically"""
        uf = getToolByName(self.context, 'acl_users')
        user = uf.getUserById(member_id)
        # this line logs the user in for the current request
        newSecurityManager(self.request, user)
        self.request.set('__ac_name', member_id)
        self.auth.login()

        # createMemberArea is safe to call many times, it checks for
        # site setting and existence before doing anything
        self.membertool.createMemberArea()
        self.membertool.setLoginTimes()

    def update_credentials(self, member_id):
        return self.auth.updateCredentials(self.request, self.response,
                                           member_id, None)
    
    @property
    def login_url(self):
        return "%s/login" % self.context.absolute_url()

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
        root = getToolByName(self.context, 'portal_url')()
        return "%s/confirm-account?key=%s" % (root, code)

    def _send_mail_to_pending_user(self, user_name, email, url):
        """ send a mail to a pending user """
        # TODO only send mail if in the pending workflow state
        root = getToolByName(self.context, 'portal_url')()
        if isinstance(user_name, str):
            user_name = user_name.decode("utf8")
        message = _(u'email_to_pending_user',
                    mapping={u'user_name':user_name,
                             u'url':url,
                             u'portal_url':root,
                             u'portal_title':self.portal_title()})
        subject = _(u'email_to_pending_user_subject',
                    mapping={u'user_name':user_name,
                             u'url':url,
                             u'portal_url':root,
                             u'portal_title':self.portal_title()})
        
        sender = EmailSender(self.portal, secureSend=True)

        sender.sendEmail(mto=email,
                         msg=message,
                         subject=subject)
