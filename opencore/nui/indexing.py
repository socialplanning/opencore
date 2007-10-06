from Missing import Value as MissingValue
from ZODB.POSException import ConflictError
from ZODB.POSException import TransactionFailedError
from Acquisition import aq_parent
from BTrees.OOBTree import OOBTree
from zope.app.annotation.interfaces import IAnnotations
from Products.CMFCore.interfaces._content import IDynamicType
from Products.CMFCore.interfaces._tools import ICatalogTool
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.CatalogTool import registerIndexableAttribute
from Products.CMFEditions.interfaces.IArchivist import ArchivistRetrieveError
from Products.OpenPlans.interfaces import IReadWorkflowPolicySupport
from Products.ZCatalog.CatalogBrains import AbstractCatalogBrain
from Products.listen.interfaces import ISearchableArchive
from Products.listen.interfaces.mailinglist import IMailingList
from Products.remember.interfaces import IReMember
from opencore.interfaces.catalog import ILastWorkflowActor, ILastModifiedAuthorId, \
     IIndexingGhost, IMetadataDictionary, ILastWorkflowTransitionDate, IMailingListThreadCount, \
     IHighestTeamRole, ILastModifiedComment
from opencore.interfaces import IOpenMembership, IOpenPage

from zope.component import adapter, queryUtility, adapts
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
        ('FieldIndex', 'mailing_list_threads', None),
        ('FieldIndex', 'highestTeamRole', None),
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
                 'lastWorkflowTransitionDate', 'mailing_list_threads',
                 'highestTeamRole', 'lastModifiedComment', PROJECT_POLICY)


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

class HighestTeamRole(object):
    """populates the highest team role metadata column for
    IOpenMemberships"""
    adapts(IOpenMembership)
    implements(IHighestTeamRole)

    def __init__(self, context):
        self.context = context

    def getValue(self):
        mship = self.context
        team = mship.getTeam()
        mem_id = mship.getId()
        return team.getHighestTeamRoleForMember(mem_id)

class LastModifiedComment(object):
    """populates the last modified comment on an IOpenPage"""
    adapts(IOpenPage)
    implements(ILastModifiedComment)

    def __init__(self, context):
        self.context = context
        self.pr = getToolByName(self.context, 'portal_repository')

    def getValue(self):
        # XXX nulling out this method b/c the last_history lookup is causing
        #     ConflictErrors and TransactionFailedErrors EVEN THOUGH WE'RE
        #     EXPLICITLY CATCHING THEM!  :-(
        return ''
        try:
            histories = self.pr.getHistory(self.context, countPurged=False)
            # most recent history versions are at the front of the list
            last_history = histories[0]
            revision_note = last_history.comment
            return revision_note
        except (IndexError, ArchivistRetrieveError, ConflictError,
                TransactionFailedError):
            return ''

@implementer(ILastModifiedAuthorId)
def authenticated_memberid(context):
    """ the last modified author is set on an annotation """
    from opencore.nui.project.metadata import ANNOT_KEY
    from Missing import Value as MissingValue
    annot = IAnnotations(context)
    annot = annot.get(ANNOT_KEY, OOBTree())
    return annot.get('lastModifiedAuthor', MissingValue)

@adapter(AbstractCatalogBrain)
@implementer(IMetadataDictionary)
def metadata_for_brain(brain):
    rid = brain.getRID()
    catalog = aq_parent(brain)
    metadata = catalog.getMetadataForRID(rid)
    metadata['getURL']=brain.getURL()
    if not metadata['Title']:
        metadata['Title']=metadata['getId']
    return metadata

@adapter(IDynamicType, ICatalogTool)
@implementer(IMetadataDictionary)
def metadata_for_portal_content(context, catalog):
    uid = '/'.join(context.getPhysicalPath())
    metadata = catalog.getMetadataForUID(uid)
    metadata['getURL']=context.absolute_url()
    if hasattr(context, 'title_or_id'):
        metadata['Title'] = context.title_or_id()
    return metadata

class MailingListThreadCount(object):
    adapts(IMailingList)
    implements(IMailingListThreadCount)

    def __init__(self, context):
        self.context = context

    def getValue(self):
        util = queryUtility(ISearchableArchive, context=self.context)
        if not util:
            return 0
        else:
            return len(util.getToplevelMessages())

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
    registerInterfaceIndexer('highestTeamRole',
                             IHighestTeamRole,
                             'getValue')
    registerInterfaceIndexer('lastModifiedComment',
                             ILastModifiedComment,
                             'getValue')
    registerInterfaceIndexer('lastModifiedAuthor', ILastModifiedAuthorId)
    registerInterfaceIndexer('mailing_list_threads', IMailingListThreadCount,
                             'getValue')



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

from Products.QueueCatalog.QueueCatalog import CHANGED

def queueObjectReindex(obj, recursive=False, skip_self=False):
    """
    This will put a recursive security reindex job for the given
    object into the async catalog queue.

    o obj - any CMF content object

    o recursive - if True, reindex all subobjects

    o skip_self - if True, don't reindex self

    Setting recursive to False and skip_self to True is a no-op.
    """
    queue = getToolByName(obj, 'portal_catalog_queue')
    path = '/'.join(obj.getPhysicalPath())

    if not recursive and not skip_self:
        queue._update(path, CHANGED)

    if recursive:
        cat = getToolByName(obj, 'portal_catalog')
        for brain in cat.unrestrictedSearchResults(path=path):
            brain_path = brain.getPath()
            if brain_path == path and skip_self:
                continue
            queue._update(brain_path, CHANGED)
