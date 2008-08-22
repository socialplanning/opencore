from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from Products.contentmigration.basemigrator.walker import CatalogWalker
from Products.contentmigration.basemigrator.walker import registerWalker
from plone.app.blob.migrations import ATFileToBlobMigrator

class FileAttachmentToBlobMigrator(ATFileToBlobMigrator):
    """
    Migrates FileAttachment types to use BLOB storage.
    """
    src_portal_type = 'FileAttachment'
    src_meta_type = 'FileAttachment'
    dst_portal_type = 'FileAttachment'
    dst_meta_type = 'ATBlobAttachment'

    def __init__(self, obj, *args, **kwargs):
        """
        Check for the 'historical' kwarg and extracts the parent
        object from its hiding place.
        """
        super(FileAttachmentToBlobMigrator, self).__init__(obj, *args, **kwargs)
        self.historical = kwargs.get('historical', False)
        if self.historical:
            self.parent = obj._historical_parent
            # don't leave our kludgey droppings around
            del obj._historical_parent
            # need to re-check the safe id generation
            while hasattr(aq_base(self.parent), self.old_id):
                self.old_id += 'X'

    def last_migrate_reindex(self):
        """ Only when we're the current version of the attachment """
        if not self.historical:
            super(FileAttachmentToBlobMigrator, self).last_migrate_reindex()


class FileAttachmentHistoryWalker(CatalogWalker):
    """
    Finds all of the objects of portal_type 'Document' in the site,
    and retrieves from the CMFEditions repository any FileAttachment
    objects attached to older versions of the page that still need to
    be migrated.
    """
    def migrate(self, objs, **kwargs):
        """
        Injects 'historical' into the kwargs so the migrator will know
        to do the right thing.  It's a bit kludgey to be passing
        around the parent in a hidden attribute on the object, but the
        other alternative is re-implementing the base class's (very
        long) migrate method.
        """
        kwargs['historical'] = True
        super(FileAttachmentHistoryWalker, self).migrate(objs, **kwargs)
        
    def walk(self):
        """
        Returns all of the historical FileAttachment objects that have
        not yet been migrated to blob storage.
        """
        catalog = self.catalog
        repo = getToolByName(catalog, 'portal_repository')
        query = {
            'portal_type': 'Document',
            }

        for brain in catalog(query):
            obj = brain.getObject()
            history = repo.getHistory(obj)
            for version in history:
                historical_obj = version.object
                for contained in historical_obj.objectValues():
                    # 'state' stuff is cargo-culted from CatalogWalker
                    # base class
                    try: state = contained._p_changed
                    except: state = 0
                    # </cargo-cult>
                    if contained.meta_type == self.src_meta_type:
                        contained._historical_parent = historical_obj
                        yield contained
                        # more cargo-culting
                        if state is None: contained._p_deactivate()
        
registerWalker(FileAttachmentHistoryWalker)
