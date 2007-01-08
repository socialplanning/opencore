import random
from zope.interface import implements, Interface
from topp.featurelets.interfaces import IFeaturelet
from opencore.featurelets.paste import BasePasteFeaturelet
from interfaces import ITaskTrackerFeatureletInstalled, ITaskTrackerContainer

class TaskTrackerFeaturelet(BasePasteFeaturelet):
    """
    A featurelet that installs a Task Tracker
    """

    implements(IFeaturelet)
    
    id = "tasks"
    title = "Task Tracker"
    installed_marker = ITaskTrackerFeatureletInstalled
    container_interface = ITaskTrackerContainer

    _info = {'menu_items': ({'title': u'Task Tracker',
                             #'description': '...',
                             'action': id,
                             #'extra': None,
                             #'order': 0,
                             #'permission': None,
                             #'filter': None,
                             #'icon': None,
                             #'_for': Interface,
                             },
                            ),
             }

    dist = 'TaskTracker'
    ep_name = 'main'
    ep_kw = {
        'cache_dir': '/tmp/tasktracker/data',
        'session_key': 'tasktracker',
        }

    def entry_point_config(self, obj):
        kwargs = BasePasteFeaturelet.entry_point_config(self, obj)
        secret = ''.join([chr(random.randint(32, 128)) for i in range(12)])
        kwargs.setdefault('session_secret', secret)
        # sqlobject.dburi is hard to set as a keyword argument; copy
        # it from database if database is there
        if 'database' in kwargs:
            kwargs.setdefault('sqlobject.dburi', kwargs['database'])
        return kwargs

        
        

