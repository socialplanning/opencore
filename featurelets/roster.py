from zope.interface import Interface
from zope.interface import implements

from OFS.interfaces import IObjectManager

from Products.OpenPlans.interfaces import IProject
from opencore.content.roster import OpenRoster

from interfaces import IFeaturelet
from interfaces import IFeatureletSupporter
from base import BaseFeaturelet

class RosterFeaturelet(BaseFeaturelet):
    """
    A featurelet providing an OpenRoster and related menu item.
    """

    implements(IFeaturelet)

    ###########################
    # IFeaturelet implemenation
    ###########################

    id = "openroster"
    # XXX create FeatureletInfo objects
    _info = {'content': ({'id':'roster', 'title':'Roster',
                          'portal_type':OpenRoster.portal_type},),
             'menu_items': ({'title': u'roster',
                             'description': u'Project Roster',
                             'action': u'roster',
                             'extra': None,
                             'order': 0,
                             'permission': None,
                             'filter': None,
                             'icon': None,
                             '_for': Interface,
                             },
                            ),
             }

    _required_interfaces = BaseFeaturelet._required_interfaces + \
                           (IProject,)

    def getConfigView(self):
        """
        See IFeaturelet.
        """
