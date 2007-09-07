from zope.interface import Interface
from zope.interface import implements

from OFS.interfaces import IObjectManager

from Products.OpenPlans.interfaces import IProject
from opencore.content.roster import OpenRoster

from topp.featurelets.interfaces import IFeaturelet
from topp.featurelets.base import BaseFeaturelet

class RosterFeaturelet(BaseFeaturelet):
    """
    A featurelet providing an OpenRoster and related menu item.
    """

    implements(IFeaturelet)

    id = "openroster"
    title = "Project Roster"

    # XXX create FeatureletInfo objects
    _info = {'content': ({'id':'proj_roster', 'title':'Project Roster',
                          'portal_type':OpenRoster.portal_type},),
             'menu_items': ({'title': u'Project Roster',
                             'description': u'Project Roster',
                             'action': u'proj_roster',
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

    def deliverPackage(self, obj):
        """
        See IFeaturelet.
        """
        BaseFeaturelet.deliverPackage(self, obj)
        objmgr = IObjectManager(obj)
        project = IProject(obj)
        roster = objmgr._getOb(self._info['content'][0]['id'])
        roster.setTeams(project.getTeams())
        return self._info
