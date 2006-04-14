from zope.interface import implements

from OFS.interfaces import IObjectManager

from Products.CMFCore.utils import getToolByName

from opencore.content.roster import OpenRoster

from interfaces import IFeaturelet
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
             'menu_items': ({'title':'roster', 'rel_url':'roster'},),
             }

    def getConfigView(self):
        """
        See IFeaturelet.
        """

    def deliverPackage(self, obj):
        """
        See IFeaturelet.
        """
        BaseFeaturelet.deliverPackage(self, obj)
        ttool = getToolByName(obj, 'portal_types')
        info = self._info
        supporter = IFeatureletSupport(obj)
        objmgr = IObjectManager(obj)

        prior_ids = tuple()
        prior_info = supporter.getFeatureletDescriptor(self.id)
        if prior_info:
            prior_content = prior_info.get('content', tuple())
            prior_ids = [item['id'] for item in prior_content]

        for item in info.get('content', tuple()):
            if item['id'] not in prior_ids:
                ttool.constructContent(item['portal_type'],
                                       objmgr, item['id'],
                                       title=item['title'])        
        return info

    def removePackage(self, obj):
        """
        See IFeaturelet.
        """
        objmgr = IObjectManager(obj)
        prior_ids = dict.fromkeys(objmgr.objectIds())
        ids = [item['id'] for item in self._info.get('content', tuple())
               if prior_ids.has_key(item['id'])]
        objmgr.manage_delObjects(ids=ids)
