from Acquisition import aq_base
from Acquisition import aq_inner
from App.Dialogs import MessageDialog
from OFS.CopySupport import CopyError
from Products.CMFCore.utils import getToolByName
from Products.contentmigration.basemigrator.walker import CatalogWalker
from Products.contentmigration.basemigrator.walker import registerWalker
from opencore.wiki.content.attachment import ATBlobAttachment
from plone.app.blob.migrations import ATFileToBlobMigrator

import sys

def historical_obj_rename(self, id, new_id):
    """
    Rename a particular sub-object stored as a historical version
    in the portal_repository
    
    Copied from Products.contentmigration.common (copied in turn from
    OFS.CopySupport)
    
    Less strict version of manage_renameObject:
        * no write look check
        * no verify object check from PortalFolder so it's allowed to rename
          even unallowed portal types inside a folder
        * no check for ob.cb_isMoveable() (which fails b/c obj._p_jar is None)
    """
    try: self._checkId(new_id)
    except: raise CopyError, MessageDialog(
                  title='Invalid Id',
                  message=sys.exc_info()[1],
                  action ='manage_main')
    ob=self._getOb(id)
    #!#if ob.wl_isLocked():
    #!#    raise ResourceLockedError, 'Object "%s" is locked via WebDAV' % ob.getId()
    #!#if not ob.cb_isMoveable():
    #!#    raise CopyError, eNotSupported % escape(id)
    #!#self._verifyObjectPaste(ob)
    #!#CopyContainer._verifyObjectPaste(self, ob)
    try:    ob._notifyOfCopyTo(self, op=1)
    except: raise CopyError, MessageDialog(
                  title='Rename Error',
                  message=sys.exc_info()[1],
                  action ='manage_main')
    self._delObject(id, suppress_events=True)
    ob = aq_base(ob)
    ob._setId(new_id)

    # Note - because a rename always keeps the same context, we
    # can just leave the ownership info unchanged.
    self._setObject(new_id, ob, set_owner=0, suppress_events=True)
    ob = self._getOb(new_id)
    ob._postCopy(self, op=1)

    #!#if REQUEST is not None:
    #!#    return self.manage_main(self, REQUEST, update_menu=1)
    return None

def _createHistoricalAttachment(type_name, container, id, *args, **kw):
    """Create an object without performing security checks
    
    invokeFactory and fti.constructInstance perform some security checks
    before creating the object. Use this function instead if you need to
    skip these checks.
    
    This method uses some code from
    CMFCore.TypesTool.FactoryTypeInformation.constructInstance
    to create the object without security checks.
    
    It doesn't finish the construction and so doesn't reinitializes the workflow.
    """
    id = str(id)
    typesTool = getToolByName(container, 'portal_types')
    fti = typesTool.getTypeInfo(type_name)
    if not fti:
        raise ValueError, 'Invalid type %s' % type_name

    # we have to do it all manually :(
    p = container.manage_addProduct[fti.product]
    m = getattr(p, fti.factory, None)
    if m is None:
        raise ValueError, ('Product factory for %s was invalid' %
                           fti.getId())

    # construct the object, truly by hand
    #m(id, *args, **kw)
    ob = ATBlobAttachment(id)
    container._setObject(id, ob, suppress_events=True)
    ob = container._getOb( id )
    ob.initializeArchetype(**kw)
    
    if hasattr(ob, '_setPortalTypeName'):
        ob._setPortalTypeName(fti.getId())
    
    return ob
    #return fti._finishConstruction(ob)


class FileAttachmentToBlobMigrator(ATFileToBlobMigrator):
    """
    Migrates FileAttachment types to use BLOB storage.
    """
    src_portal_type = 'FileAttachment'
    src_meta_type = 'FileAttachment'
    dst_portal_type = 'FileAttachment'
    dst_meta_type = 'ATBlobAttachment'


class HistoricalAttachmentToBlobMigrator(FileAttachmentToBlobMigrator):
    """
    Migrates historical file attachments stored in portal_repository.
    """
    def __init__(self, obj, *args, **kwargs):
        """
        Extracts the parent object from its hiding place.
        """
        obj = aq_inner(obj)
        FileAttachmentToBlobMigrator.__init__(self, obj, *args, **kwargs)
        # it's stored in a tuple to preserve acq settings
        self.parent = obj._historical_parent[0]
        # don't leave our kludgey droppings around
        del obj._historical_parent
        # need to re-check the safe id generation
        while hasattr(aq_base(self.parent), self.old_id):
            self.old_id += 'X'

    def last_migrate_reindex(self):
        """ Override base implementation w/ a null """
        pass

    def renameOld(self):
        """
        Use our own rename function that doesn't make the
        ob.cb_isMoveable() check, which fails b/c historical objects
        have None value for the _p_jar attribute.
        """
        historical_obj_rename(self.parent, self.orig_id, self.old_id)

    def createNew(self):
        """
        Create the new object, bypassing all the default ClassGen
        constructor stuff b/c historical containers barf on it.
        """
        _createHistoricalAttachment(self.dst_portal_type, self.parent,
                                    self.new_id, **self.schema)
        self.new = getattr(aq_inner(self.parent).aq_explicit,
                           self.new_id)

    def remove(self):
        """
        Use the low level API and suppress events.
        """
        self.parent._delObject(self.old_id, suppress_events=True)
        

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
        CatalogWalker.migrate(self, objs, **kwargs)
        
    def walk(self):
        """
        Returns all of the historical FileAttachment objects that have
        not yet been migrated to blob storage.
        """
        catalog = self.catalog
        repo = getToolByName(catalog, 'portal_repository')
        hstor = getToolByName(catalog, 'portal_historiesstorage')
        zvc_repo = hstor.zvc_repo
        query = {
            'portal_type': 'Document',
            }

        for brain in catalog(query):
            obj = brain.getObject()
            history = repo.getHistory(obj)
            real_history = zvc_repo._histories.byValue(history)[0][0]._versions
            assert len(history) == len(real_history)
            i = 0
            for version in history:
                i += 1
                historical_obj = version.object
                for contained in historical_obj.objectValues():
                    # 'state' stuff is cargo-culted from CatalogWalker
                    # base class
                    try: state = contained._p_changed
                    except: state = 0
                    # </cargo-cult>
                    if contained.meta_type == self.src_meta_type:
                        # use a tuple to avoid weird acq wrapping
                        contained._historical_parent = (historical_obj,)
                        orig_id = contained.getId()
                        yield contained
                        # man this is ugly... after the attachment has
                        # been migrated we need to retrieve the new
                        # copy and stuff it back down into the real
                        # persistent history storage
                        new_attachment = aq_base(historical_obj._getOb(orig_id))
                        key = real_history.keys()[-i]
                        real_hist_obj = aq_base(real_history[key]._data._object.object)
                        real_hist_obj._delObject(orig_id, suppress_events=True)
                        real_hist_obj._setObject(orig_id, new_attachment,
                                                 suppress_events=True)
                        # more cargo-culting
                        if state is None: contained._p_deactivate()
        
registerWalker(FileAttachmentHistoryWalker)
