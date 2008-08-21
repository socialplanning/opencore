from Products.Archetypes.public import registerType
from opencore.configuration import PROJECTNAME
from plone.app.blob.content import ATBlob

class ATBlobAttachment(ATBlob):
    """A file attachment"""
    portal_type = meta_type = 'ATBlobAttachment'

registerType(ATBlobAttachment, package=PROJECTNAME)
