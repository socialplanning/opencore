from Products.Archetypes.tests.ArchetypesTestCase import ArcheSiteTestCase
from Products.CMFCore.utils  import getToolByName
from Products.OpenPlans.Extensions.Install import migrateATDocToOpenPage as migrateOpenPage
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase
from opencore.testing.layer import SiteSetupLayer, OpenPlansLayer
from opencore.testing.utils import makeContent, getPortal, login_portal_owner
from utils import installConfiguredProducts
import Products.OpenPlans.config as config

# This is the test case. You will have to add test_<methods> to your
# class in order to assert things about your Product.
class OpenPlansTestCase(ArcheSiteTestCase):

    layer = OpenPlansLayer

    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)
        self.loginAsPortalOwner()
        
        # Because we add skins this needs to be called. Um... ick.
        self._refreshSkinData()
        self.login()
        mdc = getToolByName(self.portal, 'portal_memberdata')
        mdc.unit_test_mode = True # suppress registration emails
        
    def tearDown(self):
        # avoid any premature tearing down
        PortalTestCase.tearDown(self)
