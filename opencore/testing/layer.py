import transaction as txn

from Testing import ZopeTestCase

from Products.CMFCore.utils  import getToolByName
from Products.PloneTestCase.layer import PloneSite, ZCML
from Products.PloneTestCase.setup import setupPloneSite
from Products.remember.tests.base import MailHostMock

from Products.OpenPlans.tests.utils import installConfiguredProducts
from opencore.testing.utility import setup_mock_http
from opencore.project.handler import add_redirection_hooks 
from utils import get_portal, get_portal_as_owner, create_test_content

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

        portal.oldMailHost = portal.MailHost
        portal.MailHost = MailHostMock()
        txn.commit()

    @classmethod
    def tearDown(cls):
        portal = get_portal_as_owner()
        del portal.MailHost
        portal.MailHost = portal.oldMailHost
        del portal.oldMailHost


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

