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
    import pdb;pdb.set_trace()
    _tt_info.uri=uri

def configure_tt_info(_context, uri):
    _context.action(
        # if more than one TT_info is registered, will raise conflict
        # warning. can be overridden after configuration
        discriminator = 'opencore.tasktracker.tt_info already registered',
        callable = set_tt_info,
        args = (uri,)
        )
