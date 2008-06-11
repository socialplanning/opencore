username = 'admin'
from AccessControl.SecurityManagement import newSecurityManager
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)
from Testing.makerequest import makerequest
app=makerequest(app)
import transaction
from zope.app.annotation import IAnnotations

n = app.openplans
md = n.portal_memberdata
ms = n.portal_membership
uf = n.acl_users
at = n.portal_actions
tt = n.portal_types
wft = n.portal_workflow
cat = n.portal_catalog
tmt = n.portal_teams

for pbrain in cat(portal_type='Document', path='/openplans/streetswiki'):
    page = pbrain.getObject()
    annot = IAnnotations(page)
    try:
        del annot['opencore.nui.wiki.wikihistory']
    except KeyError:
        print 'no history annotation on %s' % page.id

transaction.get().note('removed wiki history cache from streetswiki pages')
transaction.commit()
