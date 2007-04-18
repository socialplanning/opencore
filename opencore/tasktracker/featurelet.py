from zope.interface import implements, Interface
from zope.component import getUtility
#from opencore.utility.interfaces import IHTTPClient 
from topp.featurelets.interfaces import IFeaturelet
from topp.featurelets.base import BaseFeaturelet

from interfaces import ITaskTrackerFeatureletInstalled, ITaskTrackerContainer
from Products.OpenPlans.interfaces import IProject

from opencore.tasktracker import uri as tt_uri
from memojito import memoizedproperty

from httplib2 import Http

class TaskTrackerFeaturelet(BaseFeaturelet):
    """
    A featurelet that installs a Task Tracker
    """

    implements(IFeaturelet)
    
    id = "tasks"
    title = "Task Tracker"
    installed_marker = ITaskTrackerFeatureletInstalled

    _info = {'menu_items': ({'title': u'tasks',
                             'description': u'Task Tracker',
                             'action': 'tasks'
                             },
                            ),
             }

    _required_interfaces = BaseFeaturelet._required_interfaces + (IProject,)

    @memoizedproperty
    def http(self):
        pass

    def _makeHttpReqAsUser(self, uri, obj, method="POST", headers=None):
        if headers is None:
            headers = dict()

        from Products.CMFCore.utils import getToolByName
        user_name = getToolByName(obj, 'portal_membership').getAuthenticatedMember().getId()
        
        scah = obj.acl_users.objectIds('Signed Cookie Auth Helper')[0]
        scah = obj.acl_users[scah]

        headers['Cookie'] = scah.generateCookie(user_name)
        headers['X-Openplans-Project'] = obj.id

        # @@ we are going to replace this with a utility(so we can do
        # mocking for tests)
        http = Http()
        return http.request(uri, method=method, headers=headers)

    def deliverPackage(self, obj):
        uri = "%s/project/initialize/" % tt_uri.get()
        response, content = self._makeHttpReqAsUser(uri, obj=obj,
                                                    headers={"X-Tasktracker-Initialize":"True"})
        if response.status != 200:
	    raise AssertionError("Project initialization failed: status %d" % response.status)
        return BaseFeaturelet.deliverPackage(self, obj)

    def removePackage(self, obj):
        uri = "%s/project/uninitialize/" % tt_uri.get()
        response, content = self._makeHttpReqAsUser(uri, obj=obj)
        if response.status != 200:
	    raise AssertionError("Terrible!")
        return BaseFeaturelet.removePackage(self, obj)
