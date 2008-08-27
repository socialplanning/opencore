import logging
from opencore.featurelets.interfaces import IListenContainer
from opencore.featurelets.interfaces import IListenFeatureletInstalled
from opencore.feed.interfaces import ICanFeed
from opencore.interfaces import IProject
from opencore.listen.mailinglist import OpenMailingList
from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IListLookup
from topp.featurelets.base import BaseFeaturelet
from topp.featurelets.interfaces import IFeaturelet
from topp.featurelets.interfaces import IFeatureletSupporter
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface import Interface
from zope.interface import alsoProvides
from zope.interface import implements

log = logging.getLogger('opencore.featurelets.listen')

class ListenFeaturelet(BaseFeaturelet):
    """
    A featurelet that installs a folder for managing listen based
    mailing lists.
    """
    implements(IFeaturelet)

    id = "listen"
    title = "Mailing lists"
    #config_view = "listen_config"
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
        alsoProvides(container, ICanFeed)
        return self._info
