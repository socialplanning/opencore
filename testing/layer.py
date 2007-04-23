from Products.CMFCore.utils  import getToolByName
from Products.PloneTestCase.layer import PloneSite, ZCML
import transaction as txn
from utils import get_portal, get_portal_as_owner, create_test_content
from Products.PloneTestCase.setup import setupPloneSite
from Products.OpenPlans.tests.utils import installConfiguredProducts
from opencore.testing.utility import setup_mock_http
from Testing import ZopeTestCase

class SiteSetupLayer(PloneSite):
    setupPloneSite()
    installConfiguredProducts()

    @classmethod
    def setUp(cls):
        portal = get_portal()
        setup_tool = portal.portal_setup
        setup_tool.setImportContext('profile-membrane:default')
        setup_tool.runAllImportSteps()

        setup_tool.setImportContext('profile-remember:default')
        setup_tool.runAllImportSteps()

        # install OpenPlans into ZTC
        ZopeTestCase.installProduct('OpenPlans')

        txn.commit()

    @classmethod
    def tearDown(cls):
        raise NotImplementedError


class OpenPlansLayer(SiteSetupLayer):
    @classmethod
    def setUp(cls):
        portal = get_portal_as_owner()
        qi = getToolByName(portal, 'portal_quickinstaller')
        qi.installProduct('OpenPlans')
        txn.commit()

    @classmethod
    def tearDown(cls):
        raise NotImplementedError


class OpencoreContent(OpenPlansLayer):
    @classmethod
    def setUp(cls):
        portal = get_portal_as_owner()
        create_test_content(portal)
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

