import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Products.ATContentTypes.tests.atcttestcase import ATCTFunctionalSiteTestCase 
from Testing.ZopeTestCase import FunctionalDocFileSuite
from Products.OpenPlans.tests.openplanstestcase import SiteSetupLayer

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS


class LiveSearchTestCase(ATCTFunctionalSiteTestCase):
    def tearDown(self):
        PortalTestCase.tearDown(self)

def siteui_setup(tc):
    # this installs opencore.siteui
    from opencore.siteui.Extensions.Install import install
    install(tc.portal)

def test_suite():
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Products.PloneTestCase import setup

    setup.setupPloneSite()

    readme = FunctionalDocFileSuite("README.txt",
                                    optionflags=optionflags,
                                    package='opencore.siteui',
                                    test_class=FunctionalTestCase,
                                    setUp=siteui_setup
                                    )

    livesearch = FunctionalDocFileSuite('livesearch.txt',
                                   package='opencore.siteui',
                                   test_class=LiveSearchTestCase,
                                   optionflags=optionflags)
    livesearch.layer = SiteSetupLayer

    return unittest.TestSuite((readme, livesearch))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
