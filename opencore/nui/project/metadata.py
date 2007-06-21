"""
selective catalog metadata handling 
"""
from zope.app.event import objectevent
from zope.interface import implements
import zope.event
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.CatalogTool import registerIndexableAttribute
from Products.CMFEditions.interfaces.IArchivist import ArchivistUnregisteredError
from opencore.interfaces import IProject
from opencore.interfaces.catalog import ILastModifiedAuthorId
from opencore.interfaces.catalog import IIndexingGhost
from Missing import MV

from Products.listen.interfaces import ISearchableMessage, IMailMessage
from zope.app.event.interfaces import IObjectModifiedEvent, IObjectCreatedEvent
from zope.component import adapter

@adapter(IObjectCreatedEvent)
def updateThreadCount(obj, event):
    print "Woohoo!"
    msg = ISearchableMessage(obj)
    if msg.isInitialMessage():
        # we'd like to just reindexObject on the list
        # but the new msg obj isn't really created yet
        # so we have to do a lot of nonsense instead
        list_path = msg.aq_parent.absolute_url_path()
        cat = getToolByName(msg, 'portal_catalog')
        md = cat.getMetadataForUID(list_path)
        threads = int(md['mailing_list_threads'])
        md['mailing_list_threads'] = str(threads + 1)
        proxy = type('proxy', (object,), md)()
        cat.catalog_object(proxy, list_path, idxs=['mailing_list_threads'])

def updateContainerMetadata(obj, event):
    parent = getattr(obj, 'aq_parent', None)
    if not (parent and IProject.providedBy(parent)):
        return

    lastmodifiedauthor = ILastModifiedAuthorId(obj)

    parentuid = '/'.join(parent.getPhysicalPath())

    catalog = getToolByName(parent, 'portal_catalog')

    # make comment conditional to team security policy...
    prox = proxy(dict(lastModifiedTitle=obj.title_or_id(),
                      ModificationDate=obj.modified(),
                      lastModifiedAuthor=lastmodifiedauthor,
                      ))

    selectiveMetadataUpdate(catalog._catalog, parentuid, prox)
    catalog._catalog.catalogObject(prox, parentuid, idxs=['modified'], update_metadata=0)
    
def notifyObjectModified(obj):
    zope.event.notify(objectevent.ObjectModifiedEvent(obj))

_marker = object()

def selectiveMetadataUpdate(catalog, uid, proxy):
    index = catalog.uids.get(uid, _marker)
    if index is _marker:
        # not a cataloged item for this catalog
        return 

    old=catalog.data[index]
    old = zip(catalog.names, old)
    
    [setattr(proxy, name, value) \
     for name, value in old \
     if value is not MV \
     and not hasattr(proxy, name)]
    
    record = catalog.recordify(proxy)
    if catalog.data.get(index, 0) != record:
        catalog.data[index] = record
        catalog._p_changed = True
        catalog.data._p_changed = True

def registerMetadataGhost(name):
    def ghoster(obj, portal, **kwargs):
        try:
            ghost=IIndexingGhost(obj)
        except TypeError:
            return
        return ghost.getValue(name)
    registerIndexableAttribute(name, ghoster)
    return ghoster

def proxy(attrs):
    obj = type('metadata proxy', (object,), attrs)()
    return obj


