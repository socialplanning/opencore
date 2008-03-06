"""
some basic opencore setups
"""
from Products.Five.site.localsite import enableLocalSiteHook
from opencore.testing import utils
from zope.app.component.hooks import setSite, setHooks
from opencore.tasktracker.testing.setup import base_tt_setup

def simple_setup(tc):
    tc._refreshSkinData()
    tc.request = tc.app.REQUEST
    tc.response = tc.request.RESPONSE
    tc.homepage = getattr(tc.portal, 'site-home')
    tc.projects = tc.portal.projects

def extended_tt_setup(tc):
    base_tt_setup(tc)
    simple_setup(tc)

def fresh_skin(tc):
    tc._refreshSkinData()

def set_portal_as_site(tc):
    setSite(tc.portal)

def hook_setup(tc):
    fresh_skin(tc)
    enableLocalSiteHook(tc.portal)
    set_portal_as_site(tc)
    setHooks()
