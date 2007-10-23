import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Products.ATContentTypes.tests.atcttestcase import ATCTFunctionalSiteTestCase 
from Testing.ZopeTestCase import FunctionalDocFileSuite
from opencore.testing.layer import SiteSetupLayer, OpencoreContent
from opencore.testing.utils import create_test_content
from Products.PloneTestCase import ptc

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS


class LiveSearchTestCase(ATCTFunctionalSiteTestCase):
    def tearDown(self):
        PortalTestCase.tearDown(self)


def test_suite():
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Products.PloneTestCase import setup
    from opencore import redirect
    from opencore.testing import *
    from opencore.siteui.interfaces import IMemberFolder, IMemberHomePage

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

    topnav = FunctionalDocFileSuite("topnav.txt",
                                    optionflags=optionflags,
                                    package='opencore.siteui',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=general_setup
                                    )

    member = FunctionalDocFileSuite("member.txt",
                                    optionflags=optionflags,
                                    package='opencore.siteui',
                                    test_class=ptc.PloneTestCase,
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
        suite.layer = OpencoreContent

    return unittest.TestSuite(ocui + (livesearch,))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
