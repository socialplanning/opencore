import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Testing.ZopeTestCase import FunctionalDocFileSuite
from Products.OpenPlans.tests.openplanstestcase import OpenPlansLayer
from opencore.testing.layer import MockHTTPWithContent
from opencore.testing import dtfactory as dtf
optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Products.PloneTestCase import setup
    from opencore.testing import alsoProvides, noLongerProvides
    from opencore import redirect
    from opencore.interfaces.message import ITransientMessage

    setup.setupPloneSite()
    def readme_setup(tc):
        orig_user = tc.portal.portal_membership.getAuthenticatedMember().getId()
        tc.loginAsPortalOwner()
        tc._refreshSkinData()
        tc.login(orig_user)

    globs = locals()
    readme = dtf.ZopeDocFileSuite("README.txt",
                                  optionflags=optionflags,
                                  package='opencore.member',
                                  test_class=FunctionalTestCase,
                                  globs = globs,
                                  setUp=readme_setup,
                                  layer=MockHTTPWithContent
                                  )

    transient = dtf.ZopeDocFileSuite('transient-message.txt',
                                 optionflags=optionflags,
                                 package='opencore.member',
                                 test_class=OpenPlansTestCase,
                                 globs=globs,
                                 )

    return unittest.TestSuite((readme, transient))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
