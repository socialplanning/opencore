from OFS.interfaces import IObjectManager

from zope.app.publisher.browser.menu import BrowserMenuItem

from Products.CMFCore.utils import getToolByName

from interfaces import IFeatureletSupporter
from interfaces import IMenuSupporter

class BaseFeaturelet(object):
    """
    Abstract base class for featurelet objects.
    """
    _required_interfaces = (IObjectManager, IMenuSupporter)
    _menu_id = 'featurelets'

    def _checkForRequiredInterfaces(self, obj):
        """
        Checks to see if the obj implements or can be adapted to all
        of the featurelet's required interfaces.
        """
        for iface in (IFeatureletSupporter,) + \
                self.getRequiredInterfaces():
            # just let adaptation raise an exception if necessary
            iface(obj)

    def getRequiredInterfaces(self):
        """
        See IFeaturelet.
        """
        return self._required_interfaces

    def _addContent(self, obj):
        """
        Adds any content that is specified by the featurelet's info.
        First checks for a previous installation of this featurelet,
        skips anything that was previously installed.

        Raises an error if content of the same id that was NOT a part
        of a previous installation of this featurelet exists.
        """
        ttool = getToolByName(obj, 'portal_types')
        info = self._info
        supporter = IFeatureletSupporter(obj)
        objmgr = IObjectManager(obj)

        prior_ids = tuple()
        prior_info = supporter.getFeatureletDescriptor(self.id)
        if prior_info is not None:
            prior_content = prior_info.get('content', tuple())
            prior_ids = [item['id'] for item in prior_content]

        for item in info.get('content', tuple()):
            if item['id'] not in prior_ids:
                ttool.constructContent(item['portal_type'],
                                       objmgr, item['id'],
                                       title=item['title'])

    def _addMenuItems(self, obj):
        """
        Registers any menu items that are specified by the
        featurelet's info.
        """
        info = self._info
        menu_id = self._menu_id
        supporter = IMenuSupporter(obj)
        menu_items = info.get('menu_items', tuple())
        for item_info in menu_items:
            item = BrowserMenuItem(obj, obj.REQUEST)
            for key, value in item_info.items():
                setattr(item, key, value)
            supporter.addMenuItem(menu_id, item)

    def deliverPackage(self, obj):
        """
        See IFeaturelet.
        """
        self._checkForRequiredInterfaces(obj)
        if self._info.get('content', None) is not None:
            self._addContent(obj)
        if self._info.get('menu_items', None) is not None:
            self._addMenuItems(obj)
        return self._info

    def _removeContent(self, obj, prior_info):
        """
        Removes any content that was added to the supporter as a
        result of a prior installation of this featurelet.  Will not
        touch any content that was not installed by this featurelet.
        """
        prior_content = prior_info.get('content', None)
        if prior_content is None:
            return

        objmgr = IObjectManager(obj)
        prior_ids = [item['id'] for item in prior_content]
        del_ids = [id_ for id_ in prior_ids if objmgr.hasObject(id_)]
        if del_ids:
            objmgr.manage_delObjects(ids=del_ids)

    def _removeMenuItems(self, obj, prior_info):
        """
        Removes any menu items that were registered with this
        supporter as a result of a prior installation of this
        featurelet.  Will not affect any menu items that were not
        installed by this featurelet.
        """
        prior_menu_items = prior_info.get('menu_items', None)
        if prior_menu_items is None:
            return

        menu_id = self._menu_id
        supporter = IMenuSupporter(obj)
        for item in prior_menu_items:
            supporter.removeMenuItem(menu_id, item.get('title'))

    def removePackage(self, obj):
        """
        See IFeaturelet.
        """
        supporter = IFeatureletSupporter(obj)
        prior_info = supporter.getFeatureletDescriptor(self.id)
        if prior_info is None:
            return
        self._removeContent(obj, prior_info)
        self._removeMenuItems(obj, prior_info)
