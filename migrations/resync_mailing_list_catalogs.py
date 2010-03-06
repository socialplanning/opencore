"""
``zopectl run resync_mailing_list_catalogs.py /openplans/projects/myproject``
 -> resyncs the ISearchableArchive catalog for each mailing list under the given path

``zopectl run resync_mailing_list_catalogs.py``
 -> resyncs the ISearchableArchive catalog for every mailing list on the site
"""

from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IListLookup
import transaction
from zope.component import getUtility

catalog_id = 'ISearchableArchive'

def resync_lists(context, path_prefix=None):
    """
    https://projects.openplans.org/opencore/ticket/2862
    """

    catalog = getToolByName(context, 'portal_catalog')

    query = dict(portal_type="Open Mailing List")
    if path_prefix is not None:
        query['path'] = path_prefix

    i = j = 0; changed = False
    for brain in catalog.unrestrictedSearchResults(**query):
        i += 1
        try:
            list_path = brain.getPath()
            archive_catalog = app.unrestrictedTraverse(
                '/'.join((list_path, catalog_id))
                )
            archive_catalog.refreshCatalog()
        except:
            continue

        changed = True; j += 1

        if changed and i % 400 == 0:
            transaction.get().note('Batch commit of mailing list catalog resync')
            transaction.commit()
            changed = False

    transaction.get().note('Final commit of mailing list catalog resync')
    transaction.commit()

    return j

from opencore.utils import setup
app = setup(app)

import sys
try:
    path_prefix = sys.argv[1]
except IndexError:
    path_prefix = None

num_resynced = resync_lists(app.openplans, path_prefix)
print "Resynced %d catalogs successfully" % num_resynced
