from opencore.testing.minimock import Mock
class TaskTrackerMock(Mock):
    class MockResponse(object):
        def __init__(self, status=200):
            self.status = status
    
    def __call__(self, *args, **kw):
        Mock.__call__(self, *args, **kw)
        if self.mock_name.endswith("request"):
            response = TaskTrackerMock.MockResponse(200)
            content = "Mock request succeeded!"
            return (response, content)

    def __repr__(self):
        return '<TaskTrackerMock %s>' % self.mock_name

from opencore.testing import alsoProvides
def mock_utility(name, provides):
    utility = TaskTrackerMock(name)
    utility.__provides__=None
    alsoProvides(utility, provides)
    return utility

from zope.component import provideUtility
from opencore.utility.interfaces import IHTTPClient
def setup_mock_tt_http():
    http = mock_utility('httplib2.Http', IHTTPClient)
    provideUtility(http, provides=IHTTPClient)

from opencore.testing.layer import MockHTTP
class MockTaskTrackerHTTP(MockHTTP):
    @classmethod
    def setUp(cls):
        setup_mock_tt_http()
