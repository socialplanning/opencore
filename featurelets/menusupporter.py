from persistent.mapping import PersistentMapping

from zope.interface import implements
from zope.app.annotation.interfaces import IAnnotations

from interfaces import IMenuSupporter

class MenuSupporter(object):
    """
    Adapts from IAnnotatable to IMenuSupporter.
    """

    implements(IMenuSupporter)
    annotations_key = "featurelets_menus"

    def __init__(self, context):
        self.context = context
        annotations = IAnnotations(context)
        key = self.annotations_key
        if not annotations.has_key(key):
            annotations[key] = PersistentMapping()
        self.storage = annotations[key]

    def _getMenuInfo(self, menu_id, create=False):
        """
        Retrieves the info mapping for the specific menu_id.  If
        'create' is True, the mapping will be created if it doesn't
        already exist.
        """
        menu_info = self.storage.get(menu_id, None)
        if menu_info is None:
            if create:
                menu_info = self.storage[menu_id] = PersistentMapping()
            else:
                menu_info = {}
        return menu_info

    def addMenuItem(self, menu_id, menu_item):
        """
        See IMenuSupporter.
        """
        menu_info = self._getMenuInfo(menu_id, create=True)
        title = menu_item.title
        if menu_info.has_key(title):
            return
        menu_info[title] = menu_item

    def removeMenuItem(self, menu_id, menu_item_title):
        """
        See IMenuSupporter.
        """
        menu_info = self._getMenuInfo(menu_id)
        menu_info.pop(menu_item_title, None)

    def getMenuItems(self, menu_id):
        """
        See IMenuSupporter.
        """
        return self._getMenuInfo(menu_id)
