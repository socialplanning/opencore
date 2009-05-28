"""
This zopectl run script will reset the FQDN of every mailing list in the
site to match what is currently set in the opencore_properties property
sheet.
"""
username = 'admin'
from AccessControl.SecurityManagement import newSecurityManager
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)
from Testing.makerequest import makerequest
app=makerequest(app)
import transaction
import sys
from zope.component import getUtility
from Products.listen.interfaces import IListLookup

n = app.openplans
md = n.portal_memberdata
ms = n.portal_membership
uf = n.acl_users
at = n.portal_actions
tt = n.portal_types
wft = n.portal_workflow
cat = n.portal_catalog
tmt = n.portal_teams

from zope.app.component.hooks import setSite
setSite(n)

listlookup = getUtility(IListLookup, context=n)

for brain in cat(portal_type='Open Mailing List'):
    try:
        ml = brain.getObject()
    except AttributeError:
        # ignore catalog ghosts
        pass
    setSite(ml)
    prefix = ml.mailto.split('@')[0]
    ml.mailto = prefix # automatically appends site FQDN
    listlookup.updateList(ml)

transaction.get().note('Syncing all mailing lists w/ site FQDN')
transaction.commit()
