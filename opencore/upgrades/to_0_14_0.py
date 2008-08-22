from Products.CMFCore.utils import getToolByName
from Products.contentmigration.walker import CustomQueryWalker
from opencore.upgrades.utils import logger
from opencore.upgrades.lib.blob_migration import FileAttachmentToBlobMigrator
from opencore.upgrades.lib.blob_migration import FileAttachmentHistoryWalker
from transaction import savepoint

def get_attachment_walker(context, historical=False):
    """ set up walker for migrating FileAttachment instances """
    portal = getToolByName(context, 'portal_url').getPortalObject()
    if historical:
        return FileAttachmentHistoryWalker(portal, FileAttachmentToBlobMigrator)
    return CustomQueryWalker(portal, FileAttachmentToBlobMigrator,
                             query={})


def migrate_attachments_to_blob(context):
    """
    Performs the migration of all current FileAttachment file data to
    ZODB BLOB storage.
    """
    walker = get_attachment_walker(context)
    savepoint(optimistic=True)
    walker.go()
    output = walker.getOutput()
    for line in output.split('\n'):
        logger.info(line)


def migrate_historical_attachments_to_blob(context):
    """
    Performs the migration of all CMFEditions historical FileAttachment
    file data to ZODB BLOB storage.
    """
    walker = get_attachment_walker(context, historical=True)
    savepoint(optimistic=True)
    walker.go()
    output = walker.getOutput()
    for line in output.split('\n'):
        logger.info(line)
