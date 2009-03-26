from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import OpencoreContent as test_layer
import doctest
import unittest

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

def test_suite():
    readme = dtf.ZopeDocFileSuite("README.txt",
                                  optionflags=optionflags,
                                  package='opencore.feature',
                                  test_class=OpenPlansTestCase,
                                  globs=locals(),
                                  layer=test_layer
                                  )
    return unittest.TestSuite((readme,))
