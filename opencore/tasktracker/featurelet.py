from zope.component import getUtility
from zope.component import adapts
from zope.interface import implements

from Products.CMFCore.utils import getToolByName

from memojito import memoizedproperty

from topp.featurelets.base import BaseFeaturelet
from topp.featurelets.interfaces import IFeaturelet
from topp.featurelets.interfaces import IFeatureletSupporter

from opencore.interfaces import IProject

from opencore.utility.interfaces import IHTTPClient
from opencore.tasktracker import uri as tt_uri
from opencore.tasktracker.interfaces import ITaskTrackerFeatureletInstalled

class TaskTrackerFeaturelet(BaseFeaturelet):
    # could we make featurlets named utilities?
    # currently featurelet all have the same state always
    """
    A featurelet that installs a Task Tracker
    """

    adapts(IFeatureletSupporter)
    implements(IFeaturelet)

    id = "tasks"
    title = "Task Tracker"
    installed_marker = ITaskTrackerFeatureletInstalled

    _required_interfaces = BaseFeaturelet._required_interfaces + (IProject,)
    _info = {'menu_items': ({'title': u'Tasks',
                             'description': u'Task tracker',
                             'action': 'tasks'
                             },
                            ),
             }
    @memoizedproperty
    def uri(self):
        return tt_uri.get()

    @property
    def init_uri(self):
        return "%s/project/initialize/" % self.uri

    @property
    def uninit_uri(self):
        return "%s/project/uninitialize/" % self.uri

    @memoizedproperty
    def http(self):
        return getUtility(IHTTPClient)

    def _makeHttpReqAsUser(self, uri, obj, method="POST", headers=None):
        if headers is None: headers = {}
        auth = obj.acl_users.credentials_signed_cookie_auth

        user_id = getToolByName(obj, 'portal_membership').getAuthenticatedMember().getId()
        headers['Cookie'] = auth.generateCookie(user_id)
        headers['X-Openplans-Project'] = obj.getId()
        return self.http.request(uri, method=method, headers=headers)

    def deliverPackage(self, obj):
        #XXX: we send both headers for now so that TT and OC can be updated
        #independently.  The first can be removed once TT is updated.
        header = {"X-Tasktracker-Initialize":"True"}        
        header = {"X-Openplans-Tasktracker-Initialize":"True"}
        response, content = self._makeHttpReqAsUser(self.init_uri, obj=obj,
                                                    headers=header)
        

        if response.status != 200:
            raise AssertionError("Project initialization failed: status %d (maybe TaskTracker isn't running?)" % response.status)
        return BaseFeaturelet.deliverPackage(self, obj)

    def removePackage(self, obj):
        response, content = self._makeHttpReqAsUser(self.uninit_uri, obj=obj)
        if response.status != 200:
            raise AssertionError("Error removing tasktracker featurelet")
        return BaseFeaturelet.removePackage(self, obj)
