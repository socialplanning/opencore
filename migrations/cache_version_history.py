from pprint import pprint 
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SpecialUsers import system
from opencore.nui.wiki.interfaces import IWikiHistory
from Products.CMFEditions.interfaces.IArchivist import ArchivistRetrieveError
from opencore.interfaces import IOpenPage
from DateTime.DateTime import DateTime

import sys
import transaction as txn

newSecurityManager(None, system)

try:
    portal = sys.argv[1]
except IndexError:
    portal = 'openplans'

portal = getattr(app, portal)
pc = portal.portal_catalog
pr = portal.portal_repository

def count():
    x = 0
    while True:
        x += 1
        yield x
        
counter = count()
def cache_history(page):
    if not IOpenPage.providedBy(page):
        return

    if getattr(page, '__HISTORY_MIGRATED__', False):
        #print "skip %s" %page
        return
    
    try:
        history = pr.getHistory(page, countPurged=False)
    except ArchivistRetrieveError, e:
        print "!!! ERROR: %s" %e
        return

    history_cache = IWikiHistory(page)

    # clear any old history ui info
    history_cache.annot.clear()
    for vd in history:
        new_history_item = dict(
            version_id=vd.version_id,
            comment=vd.comment,
            author=vd.sys_metadata['principal'],
            modification_date=DateTime(vd.sys_metadata['timestamp']),
            )
        history_cache.annot[vd.version_id] = new_history_item
        page.__HISTORY_MIGRATED__=True
        page._p_changed=True
    txn.commit()
    counter.next()

_ghosts = []

try:
    for brain in pc(portal_type="Document"):
        try:
            page = brain.getObject()
            page._p_jar.sync()
        except AttributeError:
            # kill ghost
            _ghosts.append(brain.getPath())
            pc.uncatalog_object(brain.getPath())
            txn.commit()
            continue
        cache_history(page)
except KeyboardInterrupt:
    print "%s ghosts removed" %len(_ghosts)
    if _ghosts:
        pprint(_ghosts)
    print "Total migrated: %s" %(counter.next() - 2)
