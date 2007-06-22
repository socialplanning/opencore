from Acquisition import aq_parent
from Products.CMFCore.interfaces._content import IDynamicType
from Products.CMFCore.interfaces._tools import ICatalogTool
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.CatalogTool import registerIndexableAttribute
from Products.OpenPlans.interfaces import IReadWorkflowPolicySupport
from Products.ZCatalog.CatalogBrains import AbstractCatalogBrain
from opencore.interfaces.catalog import ILastWorkflowActor, ILastModifiedAuthorId, \
     IIndexingGhost, IMetadataDictionary, ILastWorkflowTransitionDate
from opencore.nui.project.metadata import registerMetadataGhost
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implements, implementer

_marker = object()

PROJECT_POLICY='project_policy'

MAILTO = 'mailto'
idxs = (('FieldIndex', PROJECT_POLICY, None),
        ('FieldIndex', MAILTO, None),
        ('DateIndex', 'made_active_date', None),
        ('FieldIndex', 'getObjSize', None),
        ('FieldIndex', 'lastModifiedAuthor', None),
        ('DateIndex', 'ModificationDate', None),
        )

mem_idxs = (('FieldIndex', 'exact_getFullname',
             {'indexed_attrs': 'getFullname'}),
            ('ZCTextIndex', 'RosterSearchableText',
             {'index_type': 'Okapi BM25 Rank',
              'lexicon_id': 'lexicon'}),
            ('FieldIndex', 'sortableLocation',
             {'indexed_attrs': 'getLocation'}),
             )

metadata_cols = ('lastWorkflowActor', 'made_active_date', 'lastModifiedAuthor',
                 'lastWorkflowTransitionDate')


class LastWorkflowActor(object):
    """
    populates the 'lastWorkflowActor' metadata column for
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

class LastWorkflowTransitionDate(object):
    """
    populates the 'lastWorkflowTransitionDate' metadata column for
    IOpenMemberships
    """
    implements(ILastWorkflowTransitionDate)
    def __init__(self, context):
        self.context = context
        self.wftool = getToolByName(self.context, 'portal_workflow')

    def getValue(self):
        wftool = self.wftool
        wf_id = wftool.getChainFor(self.context)[0]
        status = wftool.getStatusOf(wf_id, self.context)
        return status.get('time')


@implementer(ILastModifiedAuthorId)
def authenticated_memberid(context):
    mtool = getToolByName(context, 'portal_membership')
    mem = mtool.getAuthenticatedMember()
    return mem.getId()

@adapter(AbstractCatalogBrain)
@implementer(IMetadataDictionary)
def metadata_for_brain(brain):
    rid = brain.getRID()
    catalog = aq_parent(brain)
    metadata = catalog.getMetadataForRID(rid)
    metadata['getURL']=brain.getURL()
    return metadata

@adapter(IDynamicType, ICatalogTool)
@implementer(IMetadataDictionary)
def metadata_for_portal_content(context, catalog):
    uid = '/'.join(context.getPhysicalPath())
    metadata = catalog.getMetadataForUID(uid)
    metadata['getURL']=context.absolute_url()
    return metadata

def createIndexes(portal, out, idxs=idxs, tool='portal_catalog'):
    catalog = getToolByName(portal, tool)
    create_indexes(out, catalog, idxs)

def createMemIndexes(portal, out):
    createIndexes(portal, out, idxs=mem_idxs, tool='membrane_tool')

def install_columns(portal, out, cols=metadata_cols):
    catalog = getToolByName(portal, 'portal_catalog')
    switch=dict([(x, True) for x in catalog.schema()])
    add = catalog.addColumn
    for col in cols:
        if not switch.has_key(col):
            add(col) 
    print >> out, 'metadata columns %s installed' %str(cols)

def registerInterfaceIndexer(idx, iface, method=None, default=None):
    """
    dynamically register z3 interface based indexes

    @param idx: name of index

    @param iface: interface to adapt object for indexing

    @param method: optional method on adapter to index

    @param default: default value to return if no adapter found
    
    """
    def indexfx(obj, portal, **kw):
        adapter = iface(obj, _marker)
        if adapter is _marker:
            return default
        if method:
            return getattr(adapter, method)()
        return adapter
    registerIndexableAttribute(idx, indexfx)

def register_indexable_attrs():
    registerInterfaceIndexer(PROJECT_POLICY, IReadWorkflowPolicySupport,
                             'getCurrentPolicyId')
    registerInterfaceIndexer('lastWorkflowActor', ILastWorkflowActor,
                             'getValue')
    registerInterfaceIndexer('lastWorkflowTransitionDate',
                             ILastWorkflowTransitionDate,
                             'getValue')
    registerInterfaceIndexer('lastModifiedAuthor', ILastModifiedAuthorId)
    
class _extra:
    """ lame holder class to support index 'extra' argument """
    pass

def create_indexes(out, catalog, idxs):
    indexes = dict([(x, True) for x in catalog.indexes()])
    added = []
    for idx, name, extra in idxs:
        if not indexes.get(name, None):
            if extra is not None:
                # *sigh*
                extra_dict = extra
                extra = _extra()
                extra.__dict__ = extra_dict
            catalog.addIndex(name, idx, extra)
            added.append(name)
            print >> out, "Added %s index" % idx
    if added:
        catalog.manage_reindexIndex(ids=added)

doCreateIndexes = create_indexes
ifaceIndexer = registerInterfaceIndexer


