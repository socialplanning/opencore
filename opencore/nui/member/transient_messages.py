from zope.interface import implements
from zope.app.annotation import IAnnotations

from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree

from OFS.SimpleItem import SimpleItem

from opencore.nui.member.interfaces import ITransientMessage

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
        cat[new_id] = msg

    def get_msgs(self, mem_id, category):
        cat = self._category_annot(mem_id, category)
        return cat.items()

    def pop(self, mem_id, category, idx):
        cat = self._category_annot(mem_id, category)
        return cat.pop(idx)
