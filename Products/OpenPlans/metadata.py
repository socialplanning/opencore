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
from Products.OpenPlans.interfaces.catalog import ILastWorkflowActor
from Products.OpenPlans.indexing import ifaceIndexer

def proxy(attrs):
    obj = type('metadata proxy', (object,), attrs)()
    return obj

def updateContainerMetadata(obj, event):
    # XXX hack to attach last modified author to open pages metadata
    lastmodifiedauthor = getAuthenticatedMemberId(obj)
    obj.lastModifiedAuthor = lastmodifiedauthor
    obj.reindexObject()
    obj._p_changed=True

    parent = getattr(obj, 'aq_parent', None)
    if not (parent and IProject.providedBy(parent)):
        return

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


# XXX this metadata ghosting infrastructure is handy, but a bit
# inflexible; it's only possible to register one metadata ghoster per
# type, which may not suffice in the future.  when the need arises,
# this should be changed to use the ifaceIndexer approach that is used
# in indexing.py

from interfaces.catalog import IIndexingGhost
class MetadataGhost(object):
    """
    provides a ghost for metadata methods, returning existing
    value.  columns that are ghosted should be set external to
    the object in question

    this implementation is used on Project objects to preserve the
    settings of certain columns when the project is modified.  these
    columns are actually informed by the page edits that happen WITHIN
    the project.
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
        if index == 0: # this is the first time indexing the object
            return default
        record = cat.data.get(index)
        table = dict(zip(cat.names, record))
        value = table.get(name, default)
        return value

def registerMetadataGhost(name):
    def ghoster(obj, portal, **kwargs):
        try:
            ghost=IIndexingGhost(obj)
        except TypeError:
            return
        return ghost.getValue(name)
    registerIndexableAttribute(name, ghoster)
    return ghoster

ghosted_cols = ('lastModifiedTitle',
                'lastModifiedAuthor',
                'lastModifiedComment',)

for col in ghosted_cols:
    registerMetadataGhost(col)

class LastWorkflowActor(object):
    """
    ghosts the 'lastWorkflowActor' metadata column for
    IOpenMemberships
    """
    implements(ILastWorkflowActor)
    def __init__(self, context):
        self.context = context
        self.wftool = getToolByName(self.context, 'portal_workflow')

    def getValue(self):
        wftool = self.wftool
        wf_id = wftool.getChainFor(self.context)[0]
        status = wftool.getStatusOf(wf_id, self.context)
        return status.get('actor')
    
ifaceIndexer('lastWorkflowActor', ILastWorkflowActor, 'getValue')

cols = ghosted_cols + ('lastWorkflowActor', 'made_active_date')
