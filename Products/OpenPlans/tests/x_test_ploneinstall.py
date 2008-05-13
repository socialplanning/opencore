"""
basic integration tests for installation

These test that openplans and dependencies installs
cleanly into a raw plone

XXX test as cmf
"""

import os, sys
import traceback
from cStringIO import StringIO

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Products.CMFCore.utils import getToolByName
from Testing import ZopeTestCase
from Products.PloneTestCase import ptc

from Products.ZCatalog import CatalogBrains

from sets import Set
import Products.OpenPlans.config as config
from Products.OpenPlans.utils import parseDepends, doc_file
from Products.OpenPlans.utils import installDepends
from Products.OpenPlans.Extensions.Install import migrateATDocToOpenPage
from Testing.ZopeTestCase import PortalTestCase, Zope2, connections, utils, base
from ZODB.DemoStorage import DemoStorage
import ZODB

from Products.PloneTestCase.setup import setupPloneSite
from Products.PloneTestCase import five
from opencore.testing.layer import PloneSite
import transaction as txn
from Products.OpenPlans.tests.utils import installConfiguredProducts

portal_name = 'o1'
extension_profiles=['membrane:default', 'remember:default']

installConfiguredProducts()
setupPloneSite(id=portal_name, extension_profiles=extension_profiles)
ZopeTestCase.installProduct('OpenPlans')

class BasePloneInstallTest(ptc.FunctionalTestCase):
    layer = PloneSite
    
    def afterSetUp(self):
        self.loginAsPortalOwner()
##         setup_tool = self.portal.portal_setup
##         setup_tool.setImportContext('profile-membrane:default')
##         setup_tool.runAllImportSteps()

##         setup_tool.setImportContext('profile-remember:default')
##         setup_tool.runAllImportSteps()

    def getPortal(self):
        return getattr(self.app, portal_name)
    
    def fail_tb(self, msg):
        """ special fail for capturing errors::good for integration testing(qi, etc) """
        out = StringIO()
        t, e, tb = sys.exc_info()
        traceback.print_exc(tb, out)
        self.fail("%s ::\n %s\n %s\n %s\n" %( msg, t, e,  out.getvalue()) )

    def installProducts(self, products):
        """ install a list of products using the quick installer """
        if type(products)!=type([]):
            products = [products,]
        qi = self.portal.portal_quickinstaller
        qi.installProducts(products, stoponerror=1)


        

class TestPloneInstall(BasePloneInstallTest):
    # @@ current causes issues with demostorage
    """ basic test for installation, qi """

    def testQIDependencies(self):
        try:
            installDepends(self.portal)
        except :
            self.fail_tb('QI install failed')

    def testQuickInstall(self):
        try:
            self.installProducts([config.PROJECTNAME])
        except :
            self.fail_tb('QI install failed')

    def testInstallMethod(self):
        from Products.OpenPlans.Extensions.Install import install
        try:
            install(self.portal)
        except:
            self.fail_tb('\nInstall from method failed')

    def test_openpage_migration(self):
        from Products.OpenPlans.Extensions.Install import install
        try:
            install(self.portal, migrate_atdoc_to_openpage=False)
        except: 
            import pdb, sys
            pdb.post_mortem(sys.exc_info()[2])
            self.fail_tb('\nInstall without migration failed')
            
        self.portal.invokeFactory('Document', 'test_doc')
        migrateATDocToOpenPage(self.portal, StringIO())
        test_doc = self.portal.test_doc
        self.failUnless(test_doc.meta_type == 'OpenPage')
        ttool = getToolByName(self.portal, 'portal_types')
        self.failIf(hasattr(ttool, 'OpenPage'))
        self.failUnless(ttool.Document.content_meta_type == 'OpenPage')

                        
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPloneInstall))
    return suite

if __name__ == '__main__':
    framework()
