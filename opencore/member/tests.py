import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Testing.ZopeTestCase import FunctionalDocFileSuite
from Products.OpenPlans.tests.openplanstestcase import OpenPlansLayer
from opencore.testing.layer import MockHTTPWithContent
optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Products.PloneTestCase import setup
    from opencore.testing import alsoProvides, noLongerProvides
    from opencore import redirect

    setup.setupPloneSite()
    def readme_setup(tc):
        orig_user = tc.portal.portal_membership.getAuthenticatedMember().getId()
        tc.loginAsPortalOwner()
        tc._refreshSkinData()
        tc.login(orig_user)

    globs = locals()
    readme = FunctionalDocFileSuite("README.txt",
                                    optionflags=optionflags,
                                    package='opencore.member',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=readme_setup
                                    )

    readme.layer = MockHTTPWithContent #yuck, shouldn't be necessary

    return unittest.TestSuite((readme,))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
