from Products.CMFPlone.CatalogTool import registerIndexableAttribute
from Products.OpenPlans.interfaces import IReadWorkflowPolicySupport
from Products.CMFCore.utils import getToolByName

_marker = object()


PROJECT_POLICY='project_policy'

def ifaceIndexer(idx, iface, method, default=None):
    """
    dynamically register z3 interface based indexes
    """
    def indexfx(obj, portal, **kw):
        adapter = iface(obj, _marker)
        if adapter is _marker:
            return default
        return getattr(adapter, method)()
        
    registerIndexableAttribute(idx, indexfx)

ifaceIndexer(PROJECT_POLICY, IReadWorkflowPolicySupport, 'getCurrentPolicyId')


class _extra:
    """ lame holder class to support index 'extra' argument """
    pass

def doCreateIndexes(out, catalog, idxs):
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


MAILTO = 'mailto'
idxs = (('FieldIndex', PROJECT_POLICY, None), ('FieldIndex', MAILTO, None),)

def createIndexes(portal, out):
    catalog = getToolByName(portal, 'portal_catalog')
    doCreateIndexes(out, catalog, idxs)


mem_idxs = (('FieldIndex', 'exact_getFullname',
             {'indexed_attrs': 'getFullname'}),
            ('ZCTextIndex', 'RosterSearchableText',
             {'index_type': 'Okapi BM25 Rank',
              'lexicon_id': 'lexicon'}),
            ('FieldIndex', 'sortableLocation',
             {'indexed_attrs': 'getLocation'}),
            )

def createMemIndexes(portal, out):
    catalog = getToolByName(portal, 'membrane_tool')
    doCreateIndexes(out, catalog, mem_idxs)
