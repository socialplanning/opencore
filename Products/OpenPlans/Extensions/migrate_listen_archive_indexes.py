from cStringIO import StringIO
from zope.component import getUtility
from Products.listen.interfaces import IListLookup
from Products.listen.interfaces import ISearchableArchive

def migrate_listen_archive_indexes(self):
    out = StringIO()

    ll = getUtility(IListLookup)
    mappings = ll.showAddressMapping()
    self.results = []
    for mapping in mappings:
        path = mapping['path']
        ml = self.context.unrestrictedTraverse(path)
        search_tool = getUtility(ISearchableArchive, context=ml)
        indexes = search_tool.indexes()
        search_tool.manage_reindexIndex(ids=indexes)
        out.write('migrated %s\n' % ml.title)

    return out.getvalue()
