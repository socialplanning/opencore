from zope.interface import implements
from zope.app.annotation import IAnnotations

from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree

from OFS.SimpleItem import SimpleItem

from opencore.interfaces.message import ITransientMessage

from lxml.html.clean import Cleaner

from zope.i18nmessageid import Message
from opencore.i18n import _
from opencore.i18n import translate


class TransientMessage(SimpleItem):
    implements(ITransientMessage)

    key = 'transient-message'

    def __init__(self, site_root):
        self.annot = IAnnotations(site_root)

    def _category_annot(self, mem_id, category):
        tm_annot = self.annot.setdefault(self.key, OOBTree())
        mem_annot = tm_annot.setdefault(mem_id, OOBTree())
        category_annot = mem_annot.setdefault(category, IOBTree())
        return category_annot

    def store(self, mem_id, category, msg):
        cat = self._category_annot(mem_id, category)
        try:
            new_id = cat.maxKey() + 1
        except ValueError:
            new_id = 0

        if isinstance(msg, Message):
            msg = translate(msg, context=self)
        else:
            msg = _(msg)

# at this point msg will always be of type Message
#         is_unicode =  isinstance(msg, unicode)
            
        cleaner = Cleaner()
        msg = cleaner.clean_html(msg)
        if msg.startswith('<p>'):
            msg = msg[3:-4]
#         if is_unicode:
#             msg = unicode(msg)
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
