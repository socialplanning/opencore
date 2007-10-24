from zope.interface import implements, Interface
from zope.component import getUtility
from opencore.utility.interfaces import IHTTPClient 
from topp.featurelets.interfaces import IFeaturelet
from topp.featurelets.base import BaseFeaturelet
from Products.CMFCore.utils import getToolByName

from interfaces import ITaskTrackerFeatureletInstalled, ITaskTrackerContainer
from Products.OpenPlans.interfaces import IProject

from opencore.tasktracker import uri as tt_uri
from memojito import memoizedproperty

class TaskTrackerFeaturelet(BaseFeaturelet):
    """
    A featurelet that installs a Task Tracker
    """

    implements(IFeaturelet)
    
    id = "tasks"
    title = "Task Tracker"
    installed_marker = ITaskTrackerFeatureletInstalled

    _info = {'menu_items': ({'title': u'Tasks',
                             'description': u'Task tracker',
                             'action': 'tasks'
                             },
                            ),
             }

    _required_interfaces = BaseFeaturelet._required_interfaces + (IProject,)

    @memoizedproperty
    def http(self):
        return getUtility(IHTTPClient)

    @memoizedproperty
    def uri(self):
        return tt_uri.get()

    @property
    def init_uri(self):
        return "%s/project/initialize/" % self.uri

    @property
    def uninit_uri(self):
        return "%s/project/uninitialize/" % self.uri

    def _makeHttpReqAsUser(self, uri, obj, method="POST", headers=None):
        if headers is None:
            headers = dict()

        user_name = getToolByName(obj, 'portal_membership').getAuthenticatedMember().getId()
        
        scah = obj.acl_users.objectIds('Signed Cookie Auth Helper')[0]
        scah = obj.acl_users[scah]

        headers['Cookie'] = scah.generateCookie(user_name)
        headers['X-Openplans-Project'] = obj.getId()
        return self.http.request(uri, method=method, headers=headers)

    def deliverPackage(self, obj):
        header = {"X-Tasktracker-Initialize":"True"}
        response, content = self._makeHttpReqAsUser(self.init_uri, obj=obj,
                                                    headers=header)
        

        if response.status != 200:
	    raise AssertionError("Project initialization failed: status %d (maybe TaskTracker isn't running?)" % response.status)
        return BaseFeaturelet.deliverPackage(self, obj)

    def removePackage(self, obj):
        response, content = self._makeHttpReqAsUser(self.uninit_uri, obj=obj)
        if response.status != 200:
            # @@ raise a real error, por fa
	    raise AssertionError("Terrible!")
        return BaseFeaturelet.removePackage(self, obj)
