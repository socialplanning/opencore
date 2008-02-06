from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Testing import ZopeTestCase
from Testing.ZopeTestCase import FunctionalDocFileSuite
from Testing.ZopeTestCase import PortalTestCase 
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import OpencoreContent as test_layer
from zope.testing import doctest
from opencore.browser import tal
import os
import sys
import unittest

#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import setup
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from pprint import pprint
    from zope.interface import alsoProvides
    from pprint import pprint
    from opencore.browser.formhandler import test_suite as octotest

    setup.setupPloneSite()
    def readme_setup(tc):
        tc._refreshSkinData()
        tc.request = tc.app.REQUEST
        tc.response = tc.request.RESPONSE
        tc.homepage = getattr(tc.portal, 'site-home')
        tc.projects = tc.portal.projects

    globs = locals()
    readme = dtf.ZopeDocFileSuite("README.txt",
                                  optionflags=optionflags,
                                  package='opencore.browser',
                                  test_class=OpenPlansTestCase,
                                  globs = globs,
                                  setUp=readme_setup,
                                  layer = test_layer                                  
                                  )
    errors = dtf.ZopeDocFileSuite("error.txt",
                                  optionflags=optionflags,
                                  package='opencore.browser',
                                  test_class=OpenPlansTestCase,
                                  globs = globs,
                                  setUp=readme_setup,
                                  layer = test_layer
                                  )

    tal_test = tal.test_suite()
    return unittest.TestSuite((readme, octotest(), tal_test, errors))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
