"""
Migration to unmake the local sites at the app root and the Plone site
root.  Run this BEFORE updating to Plone 3-based opencore, version 0.13.
"""

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SpecialUsers import system
import sys
import transaction

newSecurityManager(None, system)

from Testing.makerequest import makerequest
app=makerequest(app)

from zope.component import getMultiAdapter
from zope.interface import Interface

try:
    portal = sys.argv[1]
except IndexError:
    portal = 'openplans'

app_view = app.unrestrictedTraverse('manage_site.html')

try:
    app_view.unmakeSite()
except ValueError:
    # already run, or "can only remove directly provided interfaces"
    if getattr(app, '__local_site_hook__', None) is not None:
        del app.__local_site_hook__

portal = getattr(app, portal)
portal_view = portal.unrestrictedTraverse('manage_site.html')
try:
    portal_view.unmakeSite()
except ValueError:
    # already run, or "can only remove directly provided interfaces"
    if getattr(portal, '__local_site_hook__', None) is not None:
        del portal.__local_site_hook__

transaction.get().note('Unmade app and portal as local sites')
transaction.commit()
