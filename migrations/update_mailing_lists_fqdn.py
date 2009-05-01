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
        ml = brain.getObject()
        mailto, old_fqdn = ml.mailto.split('@')
        if old_fqdn == new_fqdn:
            continue

        ml.mailto = mailto
        lookup_utility.updateList(ml)
        changed = True

        if changed and i % 400 == 0:
            transaction.commit()
            changed = False

    transaction.commit()

