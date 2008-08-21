from Products.CMFCore.utils import getToolByName
from Products.contentmigration.walker import CustomQueryWalker
from opencore.upgrades.utils import logger
from opencore.upgrades.lib.blob_migrator import FileAttachmentToBlobMigrator
from transaction import savepoint

def get_attachment_migration_walker(context):
    """ set up walker for migrating FileAttachment instances """
    portal = getToolByName(context, 'portal_url').getPortalObject()
    return CustomQueryWalker(portal, FileAttachmentToBlobMigrator,
                             query={})

def migrate_attachments_to_blob(context):
    """
    Performs the migration of all FileAttachment file data to ZODB
    BLOB storage.
    """
    walker = get_attachment_migration_walker(context)
    savepoint(optimistic=True)
    walker.go()
    output = walker.getOutput()
    for line in output.split('\n'):
        logger.info(line)

