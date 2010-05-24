"""
Prints name,email for all members active in the last MONTHS months.
Run this via `zopectl run`.


"""
MONTHS = 18
username = 'admin'
from AccessControl.SecurityManagement import newSecurityManager
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)
from Testing.makerequest import makerequest
app=makerequest(app)

cat = app.openplans.portal_catalog

import DateTime
date = DateTime.now() - (30 * MONTHS)

allmbrains = cat(portal_type='OpenMember', review_state='public')
active = [x.getObject() for x in allmbrains if x.modified >= date]
print '\n'.join('%s,%s' % (x.getId(), x.getEmail()) for x in active)
