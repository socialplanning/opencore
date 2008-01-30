from OFS.SimpleItem import SimpleItem
from minimock import Mock, HTTPMock
from opencore.configuration.setuphandlers import register_local_utility
from opencore.cabochon.interfaces import ICabochonClient
from opencore.testing import alsoProvides
from opencore.utility.interfaces import IHTTPClient
from zope.app.component.hooks import getSite
from zope.component import queryUtility
from zope.component import provideUtility
from zope.interface import implements

def mock_utility(name, provides, cls=Mock):
    """
    a mock utility factory
    """
    utility = cls(name)
    utility.__provides__=None
    alsoProvides(utility, provides)
    return utility

def setup_mock_http():
    http = mock_utility('httplib2.Http', IHTTPClient, cls=HTTPMock)
    provideUtility(http, provides=IHTTPClient)

def setup_cabochon_mock(portal):
    # the cabochon utility is a local utility, so we need to remove it first if it already exists

    if queryUtility(ICabochonClient, context=portal):
        portal.utilities.manage_delObjects(['ICabochonClient'])
    site_manager = portal.getSiteManager()
    site_manager.registerUtility(ICabochonClient, StubCabochonClient())


class StubCabochonClient(SimpleItem):
    """stub class used to monkey patch cabochon for unit tests"""
    implements(ICabochonClient)

    def notify_project_deleted(self, uri):
        print 'opencore.testing.utility.StubCabochonClient: uri: %s' % uri
