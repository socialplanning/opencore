from zope.interface import implements
from zope.component import getUtility

from Products.CMFCore.utils import getToolByName

from memojito import memoizedproperty

from Products.OpenPlans.interfaces import IProject

from topp.featurelets.base import BaseFeaturelet
from topp.featurelets.interfaces import IFeaturelet

from opencore.utility.interfaces import IHTTPClient

class SatelliteFeaturelet(BaseFeaturelet):
    """
    A base featurelet class for featurelets that install
    zope-external services and communicate with their
    external services via HTTP calls.
    """

    implements(IFeaturelet)
    _required_interfaces = BaseFeaturelet._required_interfaces + (IProject,)

    id = "satellite"
    title = "Satellite"
    installed_marker = None

    _info = {'menu_items': ({'title': u'satellite',
                             'description': u'Satellite',
                             'action': 'satellite'
                             },
                            ),
             }
    
    @memoizedproperty
    def http(self):
        return getUtility(IHTTPClient)

    @property
    def init_uri(self):
        raise NotImplementedError

    @property
    def uninit_uri(self):
        raise NotImplementedError

    def _makeHttpReqAsUser(self, uri, obj, method="POST", headers=None):
        if headers is None: headers = {}
        auth = obj.acl_users.credentials_signed_cookie_auth

        user_id = getToolByName(obj, 'portal_membership').getAuthenticatedMember().getId()
        headers['Cookie'] = auth.generateCookie(user_id)
        headers['X-Openplans-Project'] = obj.getId()
        return self.http.request(uri, method=method, headers=headers)

    def deliverPackage(self, obj, extra_headers = None,
                       fail_msg = "Featurelet installation failed with status code %d"):
        uri = self.init_uri
        response, content = self._makeHttpReqAsUser(uri, obj, headers=extra_headers)

        if response.status != 200:
            if '%d' not in fail_msg:
                fail_msg = '%s%s' % (fail_msg, ': status code %d')
            raise AssertionError(fail_msg % response.status)
        return BaseFeaturelet.deliverPackage(self, obj)

    def removePackage(self, obj, extra_headers = None,
                      fail_msg = "Featurelet removal failed with status code %d"):
        uri = self.uninit_uri
        response, content = self._makeHttpReqAsUser(uri, obj, headers=extra_headers)

        if response.status != 200:
            if '%d' not in fail_msg:
                fail_msg = '%s%s' % (fail_msg, ': status code %d')
            raise AssertionError(fail_msg % response.status)
        return BaseFeaturelet.removePackage(self, obj)
