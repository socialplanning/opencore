from Acquisition import Implicit
from minimock import HTTPMock, ConfigMock
from minimock import Mock
from opencore.testing import alsoProvides
from opencore.utility.interfaces import IHTTPClient
from opencore.utility.interfaces import IProvideSiteConfig
from zope.component import provideUtility
from Products.MailHost.interfaces import IMailHost

class MailHostMock(Implicit):
    """
    mock up the send method so that emails do not actually get sent
    during automated tests
    """
    def __init__(self, name):
        self.messages = []
        self.name = name
    def send(self, msg, mto=None, mfrom=None, subject=None):
        msg = {'msg': msg,
               'mto': mto,
               'mfrom': mfrom,
               'subject': subject,
               }
        self.messages.append(msg)
    secureSend = send
    def validateSingleEmailAddress(self, email):
        return True

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

def setup_mock_mailhost(portal):
    portal._oldMailHost = portal.MailHost
    mailhost = mock_utility('Products.SecureMailHost.SecureMailHost.SecureMailHost',
                            IMailHost, cls=MailHostMock)
    portal.MailHost = mailhost
    sm = portal.getSiteManager()
    sm.registerUtility(mailhost, provided=IMailHost)

def teardown_mock_mailhost(portal):
    del portal.MailHost
    portal.MailHost = portal._oldMailHost
    del portal._oldMailHost

def setup_mock_config():
    config = mock_utility('config', IProvideSiteConfig, cls=ConfigMock)
    provideUtility(config, provides=IProvideSiteConfig)
