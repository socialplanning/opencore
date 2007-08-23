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