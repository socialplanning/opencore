username = 'admin'
from AccessControl.SecurityManagement import newSecurityManager
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)
from Testing.makerequest import makerequest
app=makerequest(app)
import transaction

n = app.openplans
md = n.portal_memberdata
ms = n.portal_membership
uf = n.acl_users
at = n.portal_actions
tt = n.portal_types
wft = n.portal_workflow
cat = n.portal_catalog
tmt = n.portal_teams
# to make it clearer below
portal = n

from opencore.nui.setup import nui_functions

woonerf_migrations = [
    'Initialize Project BTrees',
    'Fix up project home pages',
    'Make project home pages relative',
    'Install Cabochon Client Utility',
    'Make profile default member page',
]

for migration in woonerf_migrations:
    migration_fn = nui_functions[migration]
    print 'running migration:', migration
    migration_fn(portal)
    print 'successfully ran migration:', migration

transaction.commit()
