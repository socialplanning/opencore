"""
some basic opencore setups
"""
from Products.Five.site.localsite import enableLocalSiteHook
from zope.app.component.hooks import setSite, setHooks

def simple_setup(tc):
    tc._refreshSkinData()
    tc.request = tc.app.REQUEST
    tc.response = tc.request.RESPONSE
    tc.homepage = getattr(tc.portal, 'site-home')
    tc.projects = tc.portal.projects

def fresh_skin(tc):
    tc._refreshSkinData()

def set_portal_as_site(tc):
    setSite(tc.portal)

def hook_setup(tc):
    fresh_skin(tc)
    set_portal_as_site(tc)
    setHooks()
