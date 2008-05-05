from Products.CMFCore.utils  import getToolByName
from Products.Five import pythonproducts
from Products.Five.site.localsite import enableLocalSiteHook
from Products.PloneTestCase.layer import PloneSite, ZCML
from Products.PloneTestCase.setup import setupPloneSite
from Testing import ZopeTestCase
from opencore.project.handler import add_redirection_hooks 
from opencore.testing.utility import setup_mock_http
from opencore.testing.utility import setup_mock_config
from topp.utils import introspection
from topp.utils.testing import layer_factory
from utils import get_portal, get_portal_as_owner, create_test_content
from utils import zinstall_products
from utils import monkey_proj_noun
from zope.app.component.hooks import setSite, setHooks
import random
import transaction as txn
from opencore.utility.interfaces import IProvideSiteConfig
from zope.component import getUtility

# i can't think of a better way to guarantee that the opencore tests
# will never use a live cabochonutility. ideally oc-cab would take
# care of mocking its utility for all tests, but i don't know how
# we could do that.
try:
    from opencore.cabochon.testing.utility import setup_cabochon_mock
except ImportError:
    setup_cabochon_mock = lambda *args: None

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


class SiteSetupLayer(PloneSite):
    setupPloneSite()

    @classmethod
    def setUp(cls):
        portal = get_portal()

        zinstall_products()
        ZopeTestCase.installProduct('OpenPlans')
        ZopeTestCase.installProduct('PleiadesGeocoder')
        enableLocalSiteHook(portal)
        setSite(portal)
        setHooks()

        txn.commit()

    @classmethod
    def tearDown(cls):
        raise NotImplementedError


class OpenPlansLayer(SiteSetupLayer):
    @classmethod
    def setUp(cls):
        # need to explicitly apply pythonproducts patches to get the
        # borg.localrole package's FactoryDispatcher to work
        pythonproducts.applyPatches()
        portal = get_portal_as_owner()

        setup_tool = portal.portal_setup
        setup_tool.setImportContext('profile-opencore.configuration:default')
        setup_tool.runAllImportSteps()

        portal.oldMailHost = portal.MailHost
        portal.MailHost = MailHostMock()

        portal.browser_id_manager = BrowserIdManagerMock()
        setup_cabochon_mock(portal)
        setup_mock_config()
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
        # Many things depend on the word for project being 'project'.
        # Here's a hack to ensure that works at content creation time,
        # regardless of your config.
        # It's OK for other tests to override this...
        monkey_proj_noun('project')
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
        getUtility(IProvideSiteConfig)._set("http://nohost:wordpress")
        txn.commit()
    
    @classmethod
    def tearDown(cls):
        raise NotImplementedError


