from minimock import Mock
from opencore.testing import alsoProvides
from zope.component import provideUtility
from opencore.utility.interfaces import IHTTPClient

def mock_utility(name, provides):
    """
    a mock utility factory
    """
    utility = Mock(name)
    utility.__provides__=None
    alsoProvides(utility, provides)
    return utility

def setup_mock_http():
    http = mock_utility('httplib2.Http', IHTTPClient)
    provideUtility(http, provides=IHTTPClient)
