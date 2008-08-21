from plone.app.blob.migrations import ATFileToBlobMigrator

class FileAttachmentToBlobMigrator(ATFileToBlobMigrator):
    """
    Migrates FileAttachment types to use BLOB storage.
    """
    src_portal_type = 'FileAttachment'
    src_meta_type = 'FileAttachment'
    dst_portal_type = 'FileAttachment'
    dst_meta_type = 'ATBlobAttachment'
