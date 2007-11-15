"""
some basic opencore setups
"""
from opencore.testing import utils
from zope.app.component.hooks import setSite

def simple_setup(tc):
    tc._refreshSkinData()
    tc.request = tc.app.REQUEST
    tc.response = tc.request.RESPONSE
    tc.homepage = getattr(tc.portal, 'site-home')
    tc.projects = tc.portal.projects

def base_tt_setup(tc):
    tc.new_request = utils.new_request()
    import opencore.tasktracker
    from zope.app.annotation.interfaces import IAttributeAnnotatable
    from zope.testing.loggingsupport import InstalledHandler
    tc.log = InstalledHandler(opencore.tasktracker.LOG)
    setSite(tc.app.plone)

def extended_tt_setup(tc):
    base_tt_setup(tc)
    simple_setup(tc)

def fresh_skin(tc):
    tc._refreshSkinData()

def set_portal_as_site(tc):
    setSite(tc.portal)
