import os
import unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from opencore.testing.layer import OpencoreContent 
from zope.app.component.hooks import setSite
from Testing.ZopeTestCase import FunctionalDocFileSuite
from opencore.testing.layer import MockHTTPWithContent as test_layer
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from opencore.testing import dtfactory as dtf
from opencore.testing.setup import simple_setup

#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    # these imports are needed inside the doctests
    from Products.CMFCore.utils import getToolByName
    from opencore.interfaces import IMemberFolder
    from opencore.interfaces.membership import IEmailInvites
    from opencore.interfaces.message import ITransientMessage
    from opencore.interfaces.pending_requests import IPendingRequests
    from opencore.testing import utils
    from pprint import pprint
    from zope.component import getUtility
    from zope.interface import alsoProvides

    img = os.path.join(os.path.dirname(__file__), 'test-portrait.jpg')
    portrait = open(img)

    def setup(tc):
        """
        Make sure the local site is set.
        """
        setSite(tc.portal)

    def teardown(tc):
        utils.unmonkey_proj_noun()
        
    globs = locals()
    readme = dtf.ZopeDocFileSuite("README.txt",
                                  optionflags=optionflags,
                                  package='opencore.member.browser',
                                  test_class=OpenPlansTestCase,
                                  globs = globs,
                                  layer = test_layer,
                                  setUp = setup,
                                  )

    member_info = dtf.ZopeDocFileSuite("member_info_test.txt",
                                       optionflags=optionflags,
                                       package='opencore.member.browser',
                                       test_class=OpenPlansTestCase,
                                       globs=globs,
                                       setUp=simple_setup,
                                       layer=OpencoreContent
                                       )


    return unittest.TestSuite((readme, member_info))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
