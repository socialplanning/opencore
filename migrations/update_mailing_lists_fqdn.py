"""
``zopectl run update_mailing_lists_fqdn.py mynew.fq.dn ``
 -> set mailing_list_fqdn and migrate lists

``zopectl run update_mailing_lists_fqdn.py``
 -> migrate lists (use existing mailing_list_fqdn setting)
"""

from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IListLookup
import transaction
from zope.component import getUtility

def update_list_mailtos(context, new_fqdn):
    """
    http://www.openplans.org/projects/opencore/lists/opencore-dev/archive/2009/03/1238095821932/forum_view#1240922987323
    """
    catalog = getToolByName(context, 'portal_catalog')
    lookup_utility = getUtility(IListLookup, context=context)

    i = 0; changed = False
    for brain in catalog.unrestrictedSearchResults(portal_type=
                                                   'Open Mailing List'):
        i += 1
        try:
            ml = brain.getObject()
        except AttributeError:
            # ignore catalog ghosts
            continue
        mailto, old_fqdn = ml.mailto.split('@')
        if old_fqdn == new_fqdn:
            continue

        ml.mailto = mailto
        lookup_utility.updateList(ml)
        changed = True

        if changed and i % 400 == 0:
            transaction.get().note('Batch commit of mailing list FQDN update')
            transaction.commit()
            changed = False

    transaction.get().note('Final commit of mailing list FQDN update')
    transaction.commit()

username = 'admin'
from AccessControl.SecurityManagement import newSecurityManager
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)
from Testing.makerequest import makerequest
app=makerequest(app)

portal = app.openplans
from zope.app.component.hooks import setSite
setSite(portal)

propsheet = getToolByName(portal, 'portal_properties').opencore_properties

import sys
try:
    new_fqdn = sys.argv[1]
    propsheet.mailing_list_fqdn = new_fqdn
except IndexError:
    new_fqdn = propsheet.mailing_list_fqdn

update_list_mailtos(portal, new_fqdn)
