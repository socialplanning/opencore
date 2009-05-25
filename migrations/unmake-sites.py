"""
Migration to unmake the local sites at the app root and the Plone site
root.  Run this BEFORE updating to Plone 3-based opencore, version 0.13.

XXX - NOTE - XXX
Sometimes this script doesn't work when you run it against a ZODB newly
copied from a Plone 2.5-based Opencore site.  In these cases, Zope fails
with an error that looks like this:

    SystemError: This object was originally created by a product that
                is no longer installed.  It cannot be updated.
                (<LocalSiteHook at broken>)

When this happens, you must use the ZMI to unmake the top level site
with the following steps:

    - start Zope in production mode (debug mode will fail at startup)
    - visit "http://path/to/zope/manage_site.html" and click the
      "Unmake site" button (note that's the path to the Zope root,
      NOT the Plone site)

After you've done this, re-run this script; it should succeed, allowing
you to move on to the migrate-p3 script.
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
