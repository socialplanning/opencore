USER_ID = 'admin' # <-- SHOULD BE A MANAGER USER DEFINED AT ZOPE ROOT
SITE_ID = 'openplans' # <-- SHOULD BE A PLONE SITE DEFINED AT ZOPE ROOT
OUTPUT_FILE = '/tmp/opencore_hotshot_profile.prof'
NUMTIMES = 10

from AccessControl.SecurityManagement import newSecurityManager
from zope.app.component.hooks import setSite
user = app.acl_users.getUser(USER_ID)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)
from Testing.makerequest import makerequest
app=makerequest(app)

import hotshot

site = app._getOb(SITE_ID)
setSite(site) 

# HERE YOU DEFINE ANY VARIABLES THAT WILL BE NEEDED LATER
fp = site._getOb('front-page')

def x():
    for x in xrange(NUMTIMES):
        # HERE YOU SHOULD INVOKE THE ACTION YOU ARE PROFILING!!!
        null = fp.atct_edit()

prof = hotshot.Profile(OUTPUT_FILE)
hsr = prof.runcall(x)

