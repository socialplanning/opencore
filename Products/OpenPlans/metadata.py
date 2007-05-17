"""
selective catalog metadata handling 
"""
from zope.app.event import objectevent
from zope.interface import implements
import zope.event
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.CatalogTool import registerIndexableAttribute
from Products.CMFEditions.interfaces.IArchivist import ArchivistUnregisteredError
from Products.OpenPlans.interfaces import IProject

def proxy(attrs):
    obj = type('metadata proxy', (object,), attrs)()
    return obj

def updateContainerMetadata(obj, event):
    parent = getattr(obj, 'aq_parent', None)
    repo = getToolByName(obj, 'portal_repository', None)
    if not (repo and parent and IProject.providedBy(parent)):
        return

    parentuid = '/'.join(parent.getPhysicalPath())

    history = []
    principal = ''
    comment = ''
    
    catalog = getToolByName(parent, 'portal_catalog')

    # make comment conditional to team security policy...

    prox = proxy(dict(lastModifiedTitle=obj.title_or_id(),
                      ModificationDate=obj.modified(),
                      lastModifiedAuthor=getAuthenticatedMemberId(parent),
                      ))

    selectiveMetadataUpdate(catalog._catalog, parentuid, prox)
    catalog._catalog.catalogObject(prox, parentuid, idxs=['modified'], update_metadata=0)
    
def notifyObjectModified(obj):
    zope.event.notify(objectevent.ObjectModifiedEvent(obj))

def addDispatcherToMethod(func, dispatch):
    def new_func(*args, **kwargs):
        obj = args[0]
        value = func(*args, **kwargs)
        dispatch(obj)
        return value
    return new_func

_marker = object()
from Missing import MV

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

def getAuthenticatedMemberId(context):
    mtool = getToolByName(context, 'portal_membership')
    mem = mtool.getAuthenticatedMember()
    id = mem.getId()
    return id

from interfaces.catalog import IIndexingGhost
class MetadataGhost(object):
    """
    provides a ghost for metadata methods, returning existing
    value.  columns that are ghosted should be set external to
    the object in question
    """
    implements(IIndexingGhost)
    def __init__(self, context):
        self.context = context
        self.catalog = getToolByName(self.context, 'portal_catalog')
        
    def getValue(self, name, default=None):
        catalog = self.catalog
        cat = catalog._catalog
        uid = '/'.join(self.context.getPhysicalPath())
        index = cat.uids.get(uid, 0)
        record = cat.data[index]
        table = dict(zip(cat.names, record))
        value = table.get(name, default)
        return value

def registerMetadataGhost(name):
    def ghoster(obj, portal, **kwargs):
        try:
            ghost=ICatalogingGhost(obj)
        except TypeError:
            return
        return ghost.getValue(name)
    return ghoster
    registerIndexableAttribute(name, ghoster)

cols = ('lastModifiedTitle',
        'lastModifiedAuthor',
        'lastModifiedComment')

for col in cols:
    registerMetadataGhost(col)
