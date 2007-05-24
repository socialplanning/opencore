"""
views pertaining to accounts -- creation, login, password reset
"""

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import transaction_note
from Products.remember.utils import getAdderUtility

from opencore.nui.opencoreview import OpencoreView

class JoinView(OpencoreView):

    def __call__(self, *args, **kw):
        if self.request.environ['REQUEST_METHOD'] == 'GET':
            return self.index(*args, **kw)
        
        context = self.context
        mdc = getToolByName(context, 'portal_memberdata')
            
        adder = getAdderUtility(context)
        type_name = adder.default_member_type
        
        id = context.generateUniqueId(type_name)
        mem = mdc.restrictedTraverse('portal_factory/%s/%s' % (type_name, id))
        transaction_note('Initiated creation of %s with id %s in %s' % \
                             (mem.getTypeInfo().getId(),
                              id,
                              context.absolute_url()))
        self.errors = {}
        self.errors = mem.validate(REQUEST=self.request,
                                   errors=self.errors,
                                   data=1, metadata=0)
        
        if not self.errors:
            return mem.do_register(id=self.request.get('id'),
                                   password=self.request.get('password'))
        else:
            return self.index(*args, **kw)
        

class ConfirmAccountView(OpencoreView):

    def do_confirmation(self, member):
        pf = getToolByName(self, "portal_workflow")
        if pf.getInfoFor(member, 'review_state') != 'pending':
            return False

        setattr(member, 'isConfirmable', True)
        pf.doActionFor(member, 'register_public')
        delattr(member, 'isConfirmable')
        return True

    def __call__(self, *args, **kw):
        key = self.request.get("key")
        
        # we need to do an unrestrictedSearch because a default search
        # will filter results by user permissions
        matches = self.membranetool.unrestrictedSearchResults(UID=key)
        
        if not matches:
            self.addPortalStatusMessage(u'Denied')
            self.request.RESPONSE.redirect(self.siteURL + '/login')
        assert len(matches) == 1
        
        member = matches[0].getObject()

        if self.do_confirmation(member):
            self.addPortalStatusMessage(u'Your account has been confirmed.')
            self.request.RESPONSE.redirect(self.siteURL + '/login')
        else:
            return "Denied"


class LoginView(OpencoreView):

    @property
    def came_from(self):
        return self.request.get('came_from')

    def __call__(self, *args, **kw):
        if self.loggedin():
            return self.request.RESPONSE.redirect(self.came_from or self.siteURL)
        return self.index(*args, **kw)

class ForgotLoginView(OpencoreView):

    def mailPassword(self, forgotten_userid):
        membership = getToolByName(self, 'portal_membership')
        if not membership.checkPermission('Mail forgotten password', self):
            raise Unauthorized, "Mailing forgotten passwords has been disabled"

        member = self.membranetool(getId=forgotten_userid)

        if member is None:
            raise ValueError, 'The username you entered could not be found'
        
        member = member[0].getObject()
        
        field = member.getEmail
        if field is None:
            raise ValueError, 'Unable to retrieve email address'
        email = field()

        from smtplib import SMTPRecipientsRefused
        try:
            pwt = getToolByName(self, "portal_password_reset")
            obj = pwt.requestReset(forgotten_userid)
            randomstring = obj['randomstring']

            mail_text = self.render_static("account_forgot_password_email.txt")
            mail_text += '\n%s/reset-password?key=%s' % (self.siteURL, randomstring)
            
            host = getToolByName(self, 'MailHost')
            host.send(mail_text,
                      mfrom="help@openplans.org",
                      mto=[email]
                      )
        except SMTPRecipientsRefused:
            # Don't disclose email address on failure
            raise SMTPRecipientsRefused('Recipient address rejected by server')

    def __call__(self, *args, **kw):
        if self.request.environ['REQUEST_METHOD'] == 'GET':
            return self.index(*args, **kw)

        user_lookup = self.request.get("__ac_name")
        if not user_lookup:
            return self.index(*args, **kw)

        brains = self.membranetool(getId=user_lookup) or self.membranetool(getEmail=user_lookup)
        if not len(brains):
            self.addPortalStatusMessage(u"You do not exist")
            return self.index(*args, **kw)

        brain = brains[0]
        userid = brain.getId
        
        self.mailPassword(userid)
        
        return "An email has been sent to you, %s" % userid  # XXX rollie?
        return self.index(*args, **kw) # XXX not really right


class DoPasswordResetView(OpencoreView):

    def __call__(self, *args, **kw):
        password = self.request.get("password")
        if not password:
            return "Failed, no password."
        userid = self.request.get("userid")
        randomstring = self.request.get("randomstring")
        pw_tool = getToolByName(self.context, "portal_password_reset")
        try:
            pw_tool.resetPassword(userid, randomstring, password)
        except: # XXX DUMB
            return "Something bad happened."
        self.addPortalStatusMessage(u'Your password has been reset')
        return self.request.RESPONSE.redirect(self.siteURL)


class PasswordResetView(OpencoreView):

    def __call__(self, *args, **kw):
        key = self.request.get('key')
        pw_tool = getToolByName(self.context, "portal_password_reset")
        
        try:
            pw_tool.verifyKey(key)
        except "InvalidRequestError": # XXX rollie?
            return "You fool! The Internet Police have already been notified of this incident. Your IP has been confiscated."
        except "ExpiredRequestError": # XXX rollie?
            return "YOU HAVE EXPIRED."
        kw['randomstring'] = key
        return self.index(*args, **kw)

    
