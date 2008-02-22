from opencore.interfaces import IOpenPage
from opencore.nui.wiki.interfaces import IWikiHistory
from Products.CMFEditions.interfaces.IArchivist import ArchivistRetrieveError
from opencore.interfaces import IOpenPage
from DateTime.DateTime import DateTime


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
