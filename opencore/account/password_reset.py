from Products.CMFCore.utils import getToolByName
from opencore.browser.formhandler import button, post_only
from opencore.account.browser import AccountView, _
from zExceptions import Forbidden


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

        pw_tool = getToolByName(self.context, "portal_password_reset")
        try:
            pw_tool.resetPassword(userid, randomstring, password)
        except 'InvalidRequestError':
            # XXX TODO redirect to 404 instead
            msg = _(u'psm_pass_reset_fail', u'Password reset attempt failed. Did you mistype your username or password?')
            self.addPortalStatusMessage(msg)
            site_url = getToolByName(self.context, 'portal_url')()
            return self.redirect(site_url)
        except 'ExpiredRequestError':
            msg = _(u'psm_pass_reset_expired', u'Your password reset request has expired. '
                    'You can <a href="login">sign in</a> again using '
                    'your old username and password or '
                    '<a href="forgot">request a new password</a> again.')
            self.addPortalStatusMessage(msg)
            site_url = getToolByName(self.context, 'portal_url')()
            return self.redirect("%s/login" % self.site_url)

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
