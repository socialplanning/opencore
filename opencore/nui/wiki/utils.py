from DateTime.DateTime import DateTime
from Products.CMFEditions.interfaces.IArchivist import ArchivistRetrieveError
from StringIO import StringIO
from itertools import count
from opencore.interfaces import IOpenPage
from opencore.interfaces import IOpenPage
from opencore.nui.wiki.interfaces import IWikiHistory
from pprint import pprint
import transaction as txn

def cache_history(page, pr):
    if not IOpenPage.providedBy(page):
        return False
    
    try:
        history = pr.getHistory(page, countPurged=False)
    except ArchivistRetrieveError, e:
        print e
        return False

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
        
    return len(history)


def migrate_history(portal, path=[], out=None, save=True, noskip=False, chatty=1, reverse=False):
    """
    * save   = commit transactions incrementally 
    * path   = path to constrain migration
    * noskip = ignore old migration flags marker
    * chatty = 0 -- no chatter
             = 1 -- basic
             > 1 -- verbose
    """
    if not out:
        out = StringIO()
    pc = portal.portal_catalog
    pr = portal.portal_repository

    brains = pc.unrestrictedSearchResults(portal_type="Document", path=path)
    if chatty:
        print "\nattempting to migrate %s @ %s" %(len(brains), path)

    counter = count()
    skipcounter = count()
    _ghosts = []
    entries = 0

    try:
        if reverse:
            brains = reversed(brains)
        for brain in brains:
            try:
                page = brain.getObject()
            except AttributeError:
                # kill ghost
                skipcounter.next()
                _ghosts.append(brain.getPath())
                pc.uncatalog_object(brain.getPath())
                if save:
                    txn.commit()
                continue

            page._p_jar.sync()
            if getattr(page, '__HISTORY_MIGRATED__', False) and not noskip:
                skipcounter.next()
                continue

            result = cache_history(page, pr)
            mcount = scount = 0

            if result:
                if save:
                    txn.commit()
                mcount = counter.next()
                entries += result
            elif result is False:
                scount = skipcounter.next()
            elif chatty > 1 and result == 0 :
                print >> out, "no history: %s" %brain.getPath()

            i = mcount + scount
            if chatty and i and not i % 100:
                print "%s docs migrated" %i
                
    except KeyboardInterrupt, e:
        print e

    print >> out, "\nTotal pages migrated: % 3s" %(counter.next() - 1)
    print >> out, "Total entries migrated: % 1s" %(entries) 
    print >> out, "Total skipped: % 10s" %(skipcounter.next() - 1)
    print >> out, "Total ghosts removed: % 3s" %len(_ghosts)
    if _ghosts and chatty:
        pprint(_ghosts, stream=out)
    return out
