"""
selective catalog metadata handling 
"""
from zope.app.event import objectevent
from zope.app.annotation.interfaces import IAnnotations
import zope.event
from BTrees.OOBTree import OOBTree
from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.CatalogTool import registerIndexableAttribute
from opencore.interfaces import IProject
from opencore.interfaces import IOpenPage
from opencore.interfaces.catalog import IIndexingGhost
from opencore.interfaces.event import IAfterProjectAddedEvent
from opencore.utils import interface_in_aq_chain
from Missing import MV

from Products.listen.interfaces import ISearchableMessage
from Products.listen.interfaces import IMailMessage
from Products.listen.interfaces import IMailingList
from zope.app.event.interfaces import IObjectModifiedEvent
from zope.component import adapter

# where the last modified author is stored
ANNOT_KEY = 'opencore.project.browser.metadata'

### XXX todo write a test for this here -egj
@adapter(IMailMessage, IObjectModifiedEvent)
def updateThreadCount(obj, event):
    msg = ISearchableMessage(obj)
    if msg.isInitialMessage():
        # we'd like to just reindexObject on the list
        # but the new msg obj isn't really created yet
        # so we have to do a lot of nonsense instead
        ml_obj = interface_in_aq_chain(msg, IMailingList)
        # sometimes we get our mailing lists wrapped in a component
        # registry, thanks to local utility weirdness, and aq_inner
        # won't even fix it
        if not IFolderish.providedBy(ml_obj.aq_parent):
            # we've got one of the weird ones, up two more steps
            ml_obj = ml_obj.aq_parent.aq_parent
        list_path = '/'.join(ml_obj.getPhysicalPath())
        cat = getToolByName(msg, 'portal_catalog')
        md = cat.getMetadataForUID(list_path)
        md['mailing_list_threads'] += 1
        proxy = type('proxy', (object,), md)()
        cat._catalog.catalogObject(proxy, list_path, idxs=['mailing_list_threads'])

def updateContainerMetadata(obj, event):
    try:
        parent = obj.aq_inner.aq_parent
    except AttributeError:
        parent = None

    if not (parent and IProject.providedBy(parent)):
        return

    parent.setModificationDate()
    parent.reindexObject(idxs=['modified'])

    
def notifyObjectModified(obj):
    zope.event.notify(objectevent.ObjectModifiedEvent(obj))

_marker = object()

# XXX this doesn't look like it's used any more
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

@adapter(IOpenPage, IObjectModifiedEvent)
def update_last_modified_author(page, event):
    """ run when a wiki page is modified to set the last modified author """

    # delegate to other method to allow setup widget to also call
    _update_last_modified_author(page)

# @@ move somewhere more reusable
def get_member(context):
    mtool = getToolByName(context, 'portal_membership')
    logged_in_user = mtool.getAuthenticatedMember()
    if logged_in_user is not None:
        user_id = logged_in_user.getId()
    else:
        user_id = 'anonymous'
    return user_id
       
def _update_last_modified_author(page, user_id=None):
    # check if user_id needs to be set
    if user_id is None:
        # find last logged in user
        user_id = get_member(page)

    # annotate page object with it
    page_annot = IAnnotations(page)
    annot = page_annot.setdefault(ANNOT_KEY, OOBTree())
    annot['lastModifiedAuthor'] = user_id

    page.reindexObject(idxs=['lastModifiedAuthor'])

    # if part of a project, annotate the project with the user id as well
    proj = interface_in_aq_chain(page.aq_inner, IProject)
    if proj is None:
        return
    proj_annot = IAnnotations(proj)
    annot = proj_annot.setdefault(ANNOT_KEY, OOBTree())
    annot['lastModifiedAuthor'] = user_id

    proj.reindexObject(idxs=['lastModifiedAuthor'])
    

def proxy(attrs):
    obj = type('metadata proxy', (object,), attrs)()
    return obj

# not sure if this belongs here, but it's a catalog update
@adapter(IAfterProjectAddedEvent)
def reindex_project_ids_for_project_creator(evt):
    proj = evt.project
    mtool = getToolByName(proj, 'portal_membership')
    mem = mtool.getAuthenticatedMember()
    assert mem is not None, "anonymous user created a project?"
    mem.reindexObject(idxs=['project_ids'])
