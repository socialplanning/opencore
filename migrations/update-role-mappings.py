"""
An alternate implementation of the workflow tool's updateRoleMappings
behaviour that commits the transaction frequently to prevent
inevitable conflict errors from such a long-running process.
"""

from AccessControl.SecurityManagement import newSecurityManager
from opencore.upgrades.utils import updateRoleMappings
username = 'admin'
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)

from Testing.makerequest import makerequest
app=makerequest(app)

portal_id = 'openplans'
txn_commit_interval = 10 # num of obs btn txn commits

portal = app._getOb(portal_id)

count = updateRoleMappings(portal, commit_interval=txn_commit_interval)
print count
