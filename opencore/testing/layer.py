from Acquisition import aq_chain
from Testing import ZopeTestCase
from Testing import makerequest
from Products.OpenPlans.Extensions.create_test_content import create_test_content
from Products.PloneTestCase.layer import PloneSite, ZCML
from Products.PloneTestCase.setup import setupPloneSite
from five.localsitemanager import make_objectmanager_site
from opencore.configuration.setuphandlers import DEPS
from opencore.project.handler import add_redirection_hooks 
from opencore.testing.utility import setup_mock_http
from opencore.testing.utility import setup_mock_mailhost
from opencore.testing.utility import teardown_mock_mailhost
from opencore.testing.utility import setup_mock_config
from opencore.utils import set_opencore_properties
from sys import stdout
from utils import get_portal_as_owner
from utils import zinstall_products
from utils import monkey_proj_noun
from zope.app.component.hooks import setSite
import random
import transaction as txn

# i can't think of a better way to guarantee that the opencore tests
# will never use a live cabochonutility. ideally oc-cab would take
# care of mocking its utility for all tests, but i don't know how
# we could do that.
try:
    from opencore.cabochon.testing.utility import setup_cabochon_mock
except ImportError:
    setup_cabochon_mock = lambda *args: None

def makerequest_decorator(orig_fn, obj):
    def new_fn(app, stdout=stdout, environ=None):
        app = orig_fn(app, stdout, environ)
        req = app.REQUEST
        chain = aq_chain(obj)
        req['PARENTS'] = chain
        return app
    return new_fn

def monkeypatch_makerequest(obj):
    """
    Monkey patches the makerequest function to add a PARENTS value
    so PTS translations won't throw an error.
    """
    makerequest.orig_makerequest = makerequest.makerequest
    makerequest.makerequest = makerequest_decorator(makerequest.makerequest,
                                                    obj)

def unmonkey_makerequest():
    makerequest.makerequest = makerequest.orig_makerequest


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
        ZopeTestCase.installProduct('PleiadesGeocoder')

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

        setup_mock_mailhost(portal)

        portal.browser_id_manager = BrowserIdManagerMock()
        setup_cabochon_mock(portal)
        setup_mock_config()
        monkeypatch_makerequest(portal)
        txn.commit()

    @classmethod
    def tearDown(cls):
        portal = get_portal_as_owner()
        teardown_mock_mailhost(portal)
        unmonkey_makerequest()
        del portal.browser_id_manager

class OpencoreContent(OpenPlansLayer):
    @classmethod
    def setUp(cls):
        portal = get_portal_as_owner()
        portal.clearCurrentSkin()
        portal.setupCurrentSkin(portal.REQUEST)
        setSite(portal)

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
        set_opencore_properties(wordpress_uri='http://nohost:wordpress',
                                context=portal)
        set_opencore_properties(tasktracker_uri='http://nohost:tasktracker',
                                context=portal)
        txn.commit()
    
    @classmethod
    def tearDown(cls):
        raise NotImplementedError


