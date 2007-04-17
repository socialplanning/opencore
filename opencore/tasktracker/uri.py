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

def set_tt_info(uri):
    _tt_info.host=uri

def configure_tt_info(_context, uri):
    _context.action(
        # if more than one DH is registered, will raise conflict
        # warning. can be overridden
        discriminator = 'opencore.tasktracker.tt_info already registered',
        callable = set_tt_info,
        args = (host, path, vhost)
        )
