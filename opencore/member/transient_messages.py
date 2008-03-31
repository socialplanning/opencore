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
from opencore.interfaces import IMemberFolder


class TransientMessage(object):
    adapts(IMemberFolder)
    implements(ITransientMessage)
    
    key = 'opencore.transientmessage'

    def __init__(self, context):
        self.member_folder = context
        self.annot = IAnnotations(context)

    def _category_annot(self, category):
        tm_annot = self.annot.setdefault(self.key, OOBTree())
        category_annot = tm_annot.setdefault(category, IOBTree())
        return category_annot

    def store(self, category, msg):
        """
        This takes an OBJECT and stores it on a per-user basis.
        If we receive a string, we're going to see if it's a message id
        and attempt to translate it.  If not, WE WILL LEAVE IT ALONE!!!
        """
        cat = self._category_annot(category)
        try:
            new_id = cat.maxKey() + 1
        except ValueError:
            new_id = 0

        if isinstance(msg, Message):
            msg = translate(msg, context=self.member_folder)
        elif isinstance(msg, basestring):
            msg = _(msg)
            
        if isinstance(msg, Message) or isinstance(msg, basestring):
            cleaner = Cleaner()
            msg = cleaner.clean_html(msg)

            # clean_html wraps plain text messages in a paragraph tag.  If
            # that has happened, we'll remove it to restore the original message.
            if msg.startswith('<p>'):
                msg = msg[3:-4]

        cat[new_id] = msg
        
    def get_msgs(self, category):
        cat = self._category_annot(category)
        return cat.items()

    def get_all_msgs(self):
        tm_annot = self.annot.setdefault(self.key, OOBTree())

        items = dict(tm_annot)
        for key in items.iterkeys():
            items[key] = dict(items[key])

        return items            

    def pop(self, category, idx):
        cat = self._category_annot(category)
        return cat.pop(idx)
