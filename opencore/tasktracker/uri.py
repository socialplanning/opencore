"""
utility, directive and helper functions for locating the active
tasktracker instance
"""
from opencore.tasktracker.interfaces import ITaskTrackerInfo
from zope.interface import implements
from zope.component import getUtility

class TaskTrackerURI(object):
    implements(ITaskTrackerInfo)
    def __init__(self, uri=None, external_uri=None):
        self.uri = uri
        self.external_uri = external_uri

_tt_info = TaskTrackerURI()

def set_tt_info(uri, external_uri=None):
    _tt_info.uri=uri
    _tt_info.external_uri = external_uri

def configure_tt_info(_context, uri, external_uri=None):
    _context.action(
        # if more than one TT_info is registered, will raise conflict
        # warning. can be overridden after configuration
        discriminator = 'opencore.tasktracker.tt_info already registered',
        callable = set_tt_info,
        args = (uri, external_uri,)
        )

def get():
    return getUtility(ITaskTrackerInfo).uri

def get_external_uri():
    return getUtility(ITaskTrackerInfo).external_uri
