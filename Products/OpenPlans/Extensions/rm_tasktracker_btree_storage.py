from StringIO import StringIO
from topp.featurelets.interfaces import IFeatureletSupporter
import transaction

def rm_tasktracker_btree_storage(self):
    """extension method to remove tt storage where self is the portal"""
    projs_with_taskstorage_removed = []
    projs_with_no_taskstorage = []

    for pbrain in self.portal_catalog(portal_type='OpenProject'):
        proj = pbrain.getObject()
        fs = IFeatureletSupporter(proj)
        installed_storage_ids = fs.getInstalledFeatureletIds()
        if 'tasks' in installed_storage_ids:
            fs.storage.pop('tasks')
            projs_with_taskstorage_removed.append(proj.id)
        else:
            projs_with_no_taskstorage.append(proj.id)

    out = StringIO()
    out.write('Projects with no tasktracker btree storage:\n')
    out.write('\n'.join(projs_with_no_taskstorage))
    out.write('\n\n')
    out.write('Projects with tasktracker btree storage removed:\n')
    out.write('\n'.join(projs_with_taskstorage_removed))
    transaction.get().note('Removed tasktracker btree storage on %d items' %
                           len(projs_with_taskstorage_removed))
    return out.getvalue()
