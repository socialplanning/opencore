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

sw = n.streetswiki
for pbrain in cat(portal_type='Document', path='/openplans/streetswiki'):
    page = pbrain.getObject()
    print 'exporting %s' % page.id
    page.manage_exportObject()

transaction.commit()
