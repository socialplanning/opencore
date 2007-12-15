from Products.CMFCore.utils  import getToolByName
from Testing import ZopeTestCase
#from Products.Five.site.localsite import enableLocalSiteHook
from Products.PloneTestCase.layer import PloneSite, ZCML
from Products.PloneTestCase.setup import setupPloneSite
from Testing import ZopeTestCase
from opencore.project.handler import add_redirection_hooks 
from opencore.testing.utility import setup_mock_http
from opencore.utils import set_opencore_properties
from topp.utils import introspection
from topp.utils.testing import layer_factory
from utils import get_portal, get_portal_as_owner, create_test_content
from utils import zinstall_products
from zope.app.component.hooks import setSite, setHooks
import random
import transaction as txn
from opencore.configuration.setuphandlers import Z_DEPS, DEPS
from five.localsitemanager import make_objectmanager_site

class MailHostMock(object):
    """
    mock up the send method so that emails do not actually get sent
    during automated tests
    """
    def __init__(self):
        self.messages = []
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


class BrowserIdManagerMock(object):
    """
    mock a browser_id_manager at the Zope root.
    """
    def __init__(self):
        self.same = True
        self._same_id = '111111111111'

    def getBrowserId(self, create=False):
        if self.same:
            return self._same_id
        else:
            return str(random.random())


# XXX Do we use the 'Install' layer at all? (ra)
class Install(ZCML):
    setupPloneSite(
        products = ('OpenPlans',) + DEPS,
        extension_profiles=[#'borg.localrole:default',
                            'opencore.configuration:default'])
    @classmethod
    def setUp(cls):
        zinstall_products()
        ZopeTestCase.installProduct('OpenPlans')
        ZopeTestCase.installPackage('borg.localrole')
        make_objectmanager_site(ZopeTestCase.app())
        txn.commit()
        
    @classmethod
    def tearDown(cls):
        raise NotImplementedError

SiteSetupLayer = Install

class OpenPlansLayer(Install, PloneSite):
    @classmethod
    def setUp(cls):
        portal = get_portal_as_owner()

        portal.clearCurrentSkin()
        portal.setupCurrentSkin(portal.REQUEST)

        portal.oldMailHost = portal.MailHost
        portal.MailHost = MailHostMock()

        portal.browser_id_manager = BrowserIdManagerMock()
        txn.commit()

    @classmethod
    def tearDown(cls):
        portal = get_portal_as_owner()
        del portal.MailHost
        portal.MailHost = portal.oldMailHost
        del portal.oldMailHost
        del portal.browser_id_manager


class OpencoreContent(OpenPlansLayer):
    @classmethod
    def setUp(cls):
        portal = get_portal_as_owner()
        create_test_content(portal)
        add_redirection_hooks(portal.projects)
        txn.commit()

    @classmethod
    def tearDown(cls):
        raise NotImplementedError

OpenCoreContent = OpencoreContent


class MockHTTP(ZCML):
    @classmethod
    def setUp(cls):
        setup_mock_http()

    @classmethod
    def tearDown(cls):
        raise NotImplementedError


class MockHTTPWithContent(OpencoreContent):
    """
    Add the mock httplib2 utility to the OpencoreContent layer.
    """
    @classmethod
    def setUp(cls):
        setup_mock_http()
        portal = get_portal_as_owner()
        set_opencore_properties(wordpress_uri='http://nohost:wordpress',
                                context=portal)
        set_opencore_properties(tasktracker_uri='http://nohost:tasktracker',
                                context=portal)
        txn.commit()
    
    @classmethod
    def tearDown(cls):
        raise NotImplementedError


