"""
AccountView: the view for some of opencore's new zope3 views.
"""
from Products.CMFCore.utils import getToolByName
from opencore.nui.opencoreview import OpencoreView
from Products.Five import BrowserView

class JoinView(OpencoreView):

    def validate(self):
        return self.context.validate(REQUEST=self.request)

    def __call__(self, *args, **kw):

        if self.request.environ['REQUEST_METHOD'] == 'GET':
            return self.index(*args, **kw)

        errors = self.validate()

        if not errors:
            return self.context.do_register(id=self.request.get('id'), password=self.request.get('password'))
        else:
            return self.index(*args, **kw)

class ConfirmAccountView(OpencoreView):

    def do_confirmation(self, member):
        pf = getToolByName(self, "portal_workflow")

        if pf.getInfoFor(member, 'review_state') != 'pending':
            return False

        pf.doActionFor(member, 'Approve member, make profile public')

    def __call__(self, *args, **kw):
        key = self.request.get("key")
        uid_tool = getToolByName(self, "uid_catalog")

        matches = uid_tool(UID=key)
        
        if not matches:
            return "You is denied, muthafuka!"
        assert len(matches) == 1
        
        member = matches[0].getObject()

        if self.do_confirmation(member):
            return "You is confirmed, yo."        
        self.request.RESPONSE.redirect('@@success')


class LoginView(OpencoreView):
    @property
    def came_from(self):
        return self.request.get('came_from')

    @property
    def login(self):
        return self.loggedin()

    def __call__(self, *args, **kw):
        if self.login:
            return self.request.RESPONSE.redirect(self.came_from or self.siteURL)
        return self.index(*args, **kw)

class ForgotLoginView(OpencoreView):
    def __call__(self, *args, **kw):
        user_lookup = self.request.get("__ac_name")
        if not user_lookup:
            return self.index(*args, **kw)

        brains = self.membranetool(getId=user_lookup) or self.membranetool(getEmail=user_lookup)
        if not len(brains):
            plone_utils = getToolByName(self.context, 'plone_utils')
            from Products.CMFPlone import PloneMessageFactory
            plone_utils.addPortalMessage(PloneMessageFactory(u'You do not exist'))
            return self.index(*args, **kw)

        brain = brains[0]
        userid = brain.getId
        
        portal_reg = getToolByName(self.context, 'portal_registration')
        portal_reg.mailPassword(userid, self.request)
        
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
            return "Failed, shit is not okay."
        plone_utils = getToolByName(self.context, 'plone_utils')
        from Products.CMFPlone import PloneMessageFactory
        plone_utils.addPortalMessage(PloneMessageFactory(u'Your password has been reset'))
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
    
