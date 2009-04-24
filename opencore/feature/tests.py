from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import OpencoreContent as test_layer
import doctest
import unittest

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

def test_suite():
    def setup(tc):
        from zope.app.component.hooks import setSite
        setSite(tc.portal)
    readme = dtf.ZopeDocFileSuite("README.txt",
                                  optionflags=optionflags,
                                  package='opencore.feature',
                                  test_class=OpenPlansTestCase,
                                  globs=locals(),
                                  layer=test_layer,
                                  setUp=setup,
                                  )
    return unittest.TestSuite((readme,))
