"""
Migration to unmake the local sites at the app root and the Plone site
root.  Run this BEFORE updating to Plone 3-based opencore, version 0.13.

DO NOT RUN THIS IF YOU ARE NOT ABOUT TO UPGRADE TO PLONE 3 AND OPENCORE 
0.13 OR LATER!
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

app_view = getMultiAdapter((app, app.REQUEST), Interface,
                           name='manage_site.html')
app_view.unmakeSite()

portal = getattr(app, portal)
portal_view = getMultiAdapter((portal, portal.REQUEST), Interface,
                              name='manage_site.html')
portal_view.unmakeSite()

transaction.get().note('Unmade app and portal as local sites')
transaction.commit()
