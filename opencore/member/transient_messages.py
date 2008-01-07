from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree
from OFS.SimpleItem import SimpleItem
from lxml.html.clean import Cleaner
from opencore.i18n import _
from opencore.i18n import translate
from opencore.interfaces.message import ITransientMessage
from zope.app.annotation import IAnnotations
from zope.i18nmessageid import Message
from zope.interface import implements
from zope.component import adapts
from opencore.interfaces import IOpenSiteRoot


class TransientMessage(object):
    adapts(IOpenSiteRoot)
    implements(ITransientMessage)
    
    key = 'transient-message'

    def __init__(self, site_root):
        self.site_root = site_root
        self.annot = IAnnotations(site_root)

    def _category_annot(self, mem_id, category):
        tm_annot = self.annot.setdefault(self.key, OOBTree())
        mem_annot = tm_annot.setdefault(mem_id, OOBTree())
        category_annot = mem_annot.setdefault(category, IOBTree())
        return category_annot

    def store(self, mem_id, category, msg):
        """
        This takes an OBJECT and stores it on a per-user basis.
        If we receive a string, we're going to see if it's a message id
        and attempt to translate it.  If not, WE WILL LEAVE IT ALONE!!!
        """
        cat = self._category_annot(mem_id, category)
        try:
            new_id = cat.maxKey() + 1
        except ValueError:
            new_id = 0

        if isinstance(msg, Message):
            msg = translate(msg, context=self.site_root)
        elif isinstance(msg, basestring):
            msg = _(msg)
            
        if isinstance(msg, Message):
            cleaner = Cleaner()
            msg = cleaner.clean_html(msg)

            # what is this for? does anyone know?
            if msg.startswith('<p>'):
                msg = msg[3:-4]

        cat[new_id] = msg
        
    def get_msgs(self, mem_id, category):
        cat = self._category_annot(mem_id, category)
        return cat.items()

    def get_all_msgs(self, mem_id):
        tm_annot = self.annot.setdefault(self.key, OOBTree())
        mem_annot = tm_annot.setdefault(mem_id, OOBTree())
        cats = [cat[0] for cat in mem_annot.items()]
        items = []
        for cat in cats:
            items.extend(list(self.get_msgs(mem_id, cat)))
        return items            

    def pop(self, mem_id, category, idx):
        cat = self._category_annot(mem_id, category)
        return cat.pop(idx)
