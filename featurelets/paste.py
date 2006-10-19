"""
Implements a base class for featurelets for PasteDeploy-accessible
WSGI apps.

The basic pattern for using this is::

    from zope.interface import implements, Interface
    from topp.featurelets.interfaces import IFeaturelet
    from opencore.featurelets.paste import BasePasteFeaturelet
    from myinterfaces import IMyFeatureletInstalled, IMyContainer

    class MyFeaturelet(BasePasteFeaturelet):

        implements(IFeaturelet)

        id = 'my_featurelet'
        title = 'My Featurelet'
        installed_marker = IMyFeatureletInstalled
        container_interface = IMyContainer
        _info = {'menu_items': ({'title': u'My Featurelet',
                                 'description': 'My feature Described',
                                 'action': id,
                                 },
                                )}

        # Distribution name:
        dist = 'MyFeature' 
        # paste.app_factory entry point name:
        ep_name = 'main' 
        # any keyword arguments that go to create the app; also you
        # can override entry_point_config:
        ep_kw = {} 

"""

from OFS.interfaces import IObjectManager
from zope.interface import directlyProvides, implements, Interface
from topp.featurelets.base import BaseFeaturelet
from topp.zwsgi.zpaste import FivePasteWSGIAppBase

class BasePasteFeaturelet(BaseFeaturelet):

    def entry_point_config(self, obj):
        """
        Override this to determine the keyword arguments to
        instantiate the WSGI app dynamically.
        """
        return self.ep_kw

    def deliverPackage(self, obj):
        """
        See IFeaturelet
        """
        BaseFeaturelet.deliverPackage(self, obj)

        objmgr = IObjectManager(obj)
        kwargs = self.entry_point_config(obj)
        bucket = FivePasteWSGIAppBase(
            self.dist, self.ep_name, **kwargs)
        objmgr._setObject(self.id, bucket)
        directlyProvides(bucket, self.container_interface)
        return self._info

    def removePackage(self, obj):
        """
        See IFeaturelet
        """
        BaseFeaturelet.removePackage(self, obj)

        objmgr = IObjectManager(obj)
        objmgr.manage_delObjects(ids=[self.id])

    def register(cls):
        """
        Registers this class as a featurelet provider.
        """
        from zope.component import getUtility
        from topp.featurelets.interfaces import IFeatureletRegistry
        flet_registry = getUtility(IFeatureletRegistry)
        flet_registry.registerFeaturelet(cls())

    register = classmethod(register)
    
