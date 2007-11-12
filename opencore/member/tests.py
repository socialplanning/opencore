from Products.OpenPlans.tests.openplanstestcase import OpenPlansLayer, OpenPlansTestCase
from Testing import ZopeTestCase
from Testing.ZopeTestCase import FunctionalDocFileSuite
from Testing.ZopeTestCase import PortalTestCase 
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import MockHTTPWithContent
from opencore.testing.layer import MockHTTPWithContent as test_layer
from zope.testing import doctest
import os
import sys
import unittest

#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Products.PloneTestCase import setup
    from opencore import redirect
    from opencore.interfaces.membership import IEmailInvites
    from opencore.interfaces.message import ITransientMessage
    from opencore.interfaces.message import ITransientMessage
    from opencore.interfaces.pending_requests import IPendingRequests
    from opencore.testing import alsoProvides, noLongerProvides
    from zope.component import getUtility

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

    pending = dtf.ZopeDocFileSuite("pending_requests.txt",
                                     optionflags=optionflags,
                                     package='opencore.member',
                                     test_class=OpenPlansTestCase,
                                     globs = globs,
                                     layer = test_layer
                                    )

    pending_multi = dtf.ZopeDocFileSuite("pending_requests_multiadapter.txt",
                                         optionflags=optionflags,
                                         package='opencore.member',
                                         test_class=OpenPlansTestCase,
                                         globs = globs,
                                         layer = test_layer                                         
                                         )

    return unittest.TestSuite((readme, transient, pending, pending_multi))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
