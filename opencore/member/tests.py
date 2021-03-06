from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import OpencoreContent
from zope.testing import doctest
from zope.app.component.hooks import setSite
import unittest

#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Products.CMFCore.utils import getToolByName
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Products.PloneTestCase import setup
    from opencore import redirect
    from opencore.interfaces.membership import IEmailInvites
    from opencore.interfaces.message import ITransientMessage
    from opencore.interfaces.message import ITransientMessage
    from opencore.interfaces.pending_requests import IPendingRequests
    from zope.interface import alsoProvides
    from zope.component import getUtility

    setup.setupPloneSite()
    def readme_setup(tc):
        orig_user = tc.portal.portal_membership.getAuthenticatedMember().getId()
        tc.loginAsPortalOwner()
        tc._refreshSkinData()
        tc.login(orig_user)
        setSite(tc.portal)

    globs = locals()
    readme = dtf.ZopeDocFileSuite("README.txt",
                                  optionflags=optionflags,
                                  package='opencore.member',
                                  test_class=FunctionalTestCase,
                                  globs = globs,
                                  setUp=readme_setup,
                                  layer=OpencoreContent
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
                                   layer=OpencoreContent
                                   )

    pending_multi = dtf.ZopeDocFileSuite("pending_requests_multiadapter.txt",
                                         optionflags=optionflags,
                                         package='opencore.member',
                                         test_class=OpenPlansTestCase,
                                         globs = globs,
                                         layer=OpencoreContent
                                         )

    subscribers = dtf.ZopeDocFileSuite("subscribers.txt",
                                       optionflags=optionflags,
                                       package='opencore.member',
                                       test_class=OpenPlansTestCase,
                                       globs = globs,
                                       layer=OpencoreContent
                                       )

    return unittest.TestSuite((readme, transient, pending, pending_multi,
                               subscribers))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
