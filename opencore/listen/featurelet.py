from zope.interface import Interface
from zope.interface import implements
from zope.interface import alsoProvides

from zope.component import getMultiAdapter
from zope.component import adapts

from topp.featurelets.interfaces import IFeaturelet
from topp.featurelets.interfaces import IFeatureletSupporter
from topp.featurelets.base import BaseFeaturelet

from opencore.listen.interfaces import IListenFeatureletInstalled
from interfaces import IListenContainer

from opencore.interfaces import IProject

class ListenFeaturelet(BaseFeaturelet):
    """
    A featurelet that installs a folder for managing listen based
    mailing lists.
    """
    adapts(IFeatureletSupporter)
    implements(IFeaturelet)

    id = "listen"
    title = "Mailing lists"
    installed_marker = IListenFeatureletInstalled
    
    _info = {'content': ({'id': 'lists', 'title': 'Mailing lists',
                          'portal_type': 'Folder'},),
             'menu_items': ({'title': u'Mailing lists',
                             'description': u'Mailing lists',
                             'action': u'lists',
                             'order': 0,
                             },
                            ),
             }

    _required_interfaces = BaseFeaturelet._required_interfaces + \
                           (IProject,)

    def deliverPackage(self, obj):
        """
        See IFeaturelet.
        """
        BaseFeaturelet.deliverPackage(self, obj)
        container = obj._getOb(self._info['content'][0]['id'])
        container.setLayout('mailing_lists')
        alsoProvides(container, IListenContainer)
        return self._info
