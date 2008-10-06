"""
Script to ensure that all indexed project_ids are correct.
Fixes bad data related to http://trac.openplans.org/errors-openplans/ticket/36

This should be run after upgrading from opencore <= 0.13.0
to opencore >= 0.14.0.

"""

from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.SpecialUsers import system
from Testing.makerequest import makerequest

from opencore.upgrades.to_0_14_0 import fix_member_indexes

app=makerequest(app)
sm = getSecurityManager()
try:
    newSecurityManager(None, system)
    fix_member_indexes(app.openplans)
finally:
    setSecurityManager(sm)

