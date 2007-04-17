"""
utility, directive and helper functions for locating the active
tasktracker instance
"""
from opencore.tasktracker.interfaces import ITaskTrackerInfo
from zope.interface import implements

class TaskTrackerURI(object):
    implements(ITaskTrackerInfo)
    def __init__(self, uri=None):
        self.uri = uri

_tt_info = TaskTrackerURI()
