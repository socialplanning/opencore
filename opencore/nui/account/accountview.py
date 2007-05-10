"""
AccountView: the view for some of opencore's new zope3 views.
"""
from Products.CMFCore.utils import getToolByName
from opencore.nui.opencoreview import OpencoreView

class JoinView(OpencoreView):
    pass
#def __call__(self, *args, **kw):
#        
#        return self.index(*args, **kw)

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
        
        return "An email has been sent to you, %s" % userid
        return self.index(*args, **kw) # XXX not really right

class PasswordResetView(OpencoreView):
    def __call__(self, *args, **kw):        
        self.request.get('key', None)
        return "foo"
