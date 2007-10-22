from memojito import memoizedproperty

from opencore.featurelets.satellite import SatelliteFeaturelet
from opencore.tasktracker import uri as tt_uri
from opencore.tasktracker.interfaces import \
    ITaskTrackerFeatureletInstalled, ITaskTrackerContainer

class TaskTrackerFeaturelet(SatelliteFeaturelet):
    """
    A featurelet that installs a Task Tracker
    """

    id = "tasks"
    title = "Task Tracker"
    installed_marker = ITaskTrackerFeatureletInstalled

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

    def deliverPackage(self, obj):
        return SatelliteFeaturelet.deliverPackage(
            self, obj,
            extra_headers = {"X-Tasktracker-Initialize":"True"})
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
