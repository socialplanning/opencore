from zope.interface import implements, Interface

from topp.featurelets.interfaces import IFeaturelet
from topp.featurelets.base import BaseFeaturelet

from interfaces import ITaskTrackerFeatureletInstalled, ITaskTrackerContainer
from Products.OpenPlans.interfaces import IProject

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

    def _makeHttpReqAsUser(self, uri, obj, method="POST", headers=None):
        if headers is None:
            headers = dict()

        from Products.CMFCore.utils import getToolByName
        user_name = getToolByName(obj, 'portal_membership').getAuthenticatedMember().getId()

        scah = obj.acl_users.objectIds('Signed Cookie Auth Helper')[0]
        scah = obj.acl_users[scah]

        headers['Cookie'] = scah.generateCookie(user_name)

        http = Http()
        return http.request(uri, method=method, headers=headers)

    def deliverPackage(self, obj):
        uri = "%s/tasks/project/initialize/" % obj.absolute_url()
        response, content = self._makeHttpReqAsUser(uri, obj=obj)
        if response.status != 200: 
	    raise AssertionError("Terrible!")
	    #            pass  #just kidding -- do something terrible instead

        return BaseFeaturelet.deliverPackage(self, obj)

    def removePackage(self, obj):
        uri = "%s/tasks/project/initialize/" % obj.absolute_url()
        response, content = self._makeHttpReqAsUser(uri, obj=obj)
        if response.status != 200:
	    raise AssertionError("Terrible!")
            #pass  #just kidding -- do something terrible instead

        return BaseFeaturelet.removePackage(self, obj)
