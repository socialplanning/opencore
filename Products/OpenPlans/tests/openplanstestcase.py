from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase

from zope.app.annotation.interfaces import IAnnotations
from plone.memoize.view import ViewMemo
from plone.memoize.instance import Memojito

from Products.CMFCore.utils  import getToolByName
from Products.Archetypes.tests.ArchetypesTestCase import ArcheSiteTestCase
from Products.OpenPlans.Extensions.Install import migrateATDocToOpenPage as migrateOpenPage

import Products.OpenPlans.config as config

from opencore.testing.layer import SiteSetupLayer, OpenPlansLayer
from opencore.testing.utils import makeContent, getPortal, login_portal_owner
from utils import installConfiguredProducts

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

    def clearMemoCache(self):
        req = self.portal.REQUEST
        annotations = IAnnotations(req)
        cache = annotations.get(ViewMemo.key, None)
        if cache is not None:
            annotations[ViewMemo.key] = dict()

    def clearInstanceCache(self, obj):
        propname = Memojito.propname
        try:
            delattr(obj, propname)
        except AttributeError:
            pass
