from DateTime.DateTime import DateTime
from Products.CMFEditions.interfaces.IArchivist import ArchivistRetrieveError
from StringIO import StringIO
from itertools import count
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


def migrate_history(portal, path=None, out=None, save=True, noskip=False, chatty=1):
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

    print >> out, "\nTotal pages migrated: %3s" % counter.next()
    print >> out, "Total entries migrated: %1s" % entries
    print >> out, "Total skipped: %10s" % skipcounter.next()
    print >> out, "Total ghosts removed: %3s" % len(_ghosts)
    if _ghosts and chatty:
        pprint(_ghosts, stream=out)
    return out

# HTML Unescaping as per the python wiki at:
# http://wiki.python.org/moin/EscapingHtml
#
# As well as per the comp.lang.python discussion at:
# http://groups.google.com/group/comp.lang.python/msg/ce3fc3330cbbac0a

import htmlentitydefs
import re
import unittest

def unescape_charref(ref):
    name = ref[2:-1]
    base = 10
    if name.startswith("x"):
        name = name[1:]
        base = 16
    return unichr(int(name, base))

def replace_entities(match):
    ent = match.group()
    if ent[1] == "#":
        return unescape_charref(ent)

    repl = htmlentitydefs.name2codepoint.get(ent[1:-1])
    if repl is not None:
        repl = unichr(repl)
    else:
        repl = ent
    return repl

def unescape(data):
    return re.sub(r"&#?[A-Za-z0-9]+?;", replace_entities, data)

class UnescapeTests(unittest.TestCase):

    def test_unescape_charref(self):
        self.assertEqual(unescape_charref(u"&#38;"), u"&")
        self.assertEqual(unescape_charref(u"&#x2014;"), u"\N{EM DASH}")
        self.assertEqual(unescape_charref(u"&#8212;"), u"\N{EM DASH}")
        self.assertEqual("These tests don't get run", "Otherwise this would fail") # XXX

    def test_unescape(self):
        self.assertEqual(
            unescape(u"&amp; &lt; &mdash; &#8212; &#x2014;"),
            u"& < %s %s %s" % tuple(u"\N{EM DASH}"*3)
            )
        self.assertEqual(unescape(u"&a&amp;"), u"&a&")
        self.assertEqual(unescape(u"a&amp;"), u"a&")
        self.assertEqual(unescape(u"&nonexistent;"), u"&nonexistent;") 
