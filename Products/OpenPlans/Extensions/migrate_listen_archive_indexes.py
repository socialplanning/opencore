from StringIO import StringIO
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
        try:
            ml = self.unrestrictedTraverse(path)
        except AttributeError:
            continue
        search_tool = getUtility(ISearchableArchive, context=ml)
        indexes = search_tool.indexes()
        try:
            search_tool.manage_reindexIndex(ids=indexes)
        except UnicodeDecodeError:
            out.write('***** codec error for list: %s\n' % ml.title)
        else:
            out.write('migrated %s\n' % ml.title)

    return out.getvalue()
