import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Products.ATContentTypes.tests.atcttestcase import ATCTFunctionalSiteTestCase 
from Testing.ZopeTestCase import FunctionalDocFileSuite
from opencore.testing.layer import SiteSetupLayer, OpenCoreContent
from opencore.testing.utils import create_test_content

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS


class LiveSearchTestCase(ATCTFunctionalSiteTestCase):
    def tearDown(self):
        PortalTestCase.tearDown(self)


def test_suite():
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Products.PloneTestCase import setup
    from zope.interface import alsoProvides
    from Products.Five.utilities.marker import erase as noLongerProvides
    from opencore import redirect

    setup.setupPloneSite()
    def general_setup(tc):
        tc._refreshSkinData()

    globs = locals()
    readme = FunctionalDocFileSuite("README.txt",
                                    optionflags=optionflags,
                                    package='opencore.siteui',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=general_setup
                                    )

    topnav = FunctionalDocFileSuite("naked/topnav.txt",
                                    optionflags=optionflags,
                                    package='opencore.siteui',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=general_setup
                                    )

    member = FunctionalDocFileSuite("member.txt",
                                    optionflags=optionflags,
                                    package='opencore.siteui',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=general_setup
                                    )

    livesearch = FunctionalDocFileSuite('livesearch.txt',
                                   package='opencore.siteui',
                                   test_class=LiveSearchTestCase,
                                   optionflags=optionflags)
    
    livesearch.layer = SiteSetupLayer

    ocui = readme, member, topnav,
    for suite in ocui:
        suite.layer = OpenCoreContent

    return unittest.TestSuite(ocui + (livesearch,))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
