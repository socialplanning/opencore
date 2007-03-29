import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Products.ATContentTypes.tests.atcttestcase import ATCTFunctionalSiteTestCase 
from Testing.ZopeTestCase import FunctionalDocFileSuite
from Products.OpenPlans.tests.openplanstestcase import SiteSetupLayer, OpenPlansLayer

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS


class LiveSearchTestCase(ATCTFunctionalSiteTestCase):
    def tearDown(self):
        PortalTestCase.tearDown(self)


def test_suite():
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Products.PloneTestCase import setup
    from opencore.testing import create_test_content
    from zope.interface import alsoProvides
    from Products.Five.utilities.marker import erase as noLongerProvides
    from opencore import redirect

    setup.setupPloneSite()
    def readme_setup(tc):
        create_test_content(tc.portal)
        tc._refreshSkinData()


    globs = locals()
    readme = FunctionalDocFileSuite("README.txt",
                                    optionflags=optionflags,
                                    package='opencore.siteui',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=readme_setup
                                    )

    livesearch = FunctionalDocFileSuite('livesearch.txt',
                                   package='opencore.siteui',
                                   test_class=LiveSearchTestCase,
                                   optionflags=optionflags)
    livesearch.layer = SiteSetupLayer
    readme.layer = OpenPlansLayer

    return unittest.TestSuite((readme, livesearch))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
