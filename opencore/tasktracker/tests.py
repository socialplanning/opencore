import os, sys, unittest
from zope.testing import doctest
from collective.testing import utils
from zope.testing import doctestunit
from zope.testing import doctest
from zope.component import testing
from Testing import ZopeTestCase as ztc
from Products.Five import zcml
from zope.app.component.hooks import setSite
from zope.interface import alsoProvides
from zope.testing.cleanup import cleanUp
from opencore.testing.layer import MockHTTPWithContent
from opencore.testing.setup import base_tt_setup
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase

def clean_CA(tc):
    return cleanUp()

import warnings; warnings.filterwarnings("ignore")

optionflags = doctest.ELLIPSIS

def test_suite():
    from zope.component import getMultiAdapter, getUtility
    from opencore.testing import *
    from opencore.utility.interfaces import IHTTPClient
    
    readme = ztc.FunctionalDocFileSuite('README.txt',
                                        package='opencore.tasktracker',
                                        optionflags=optionflags,
                                        test_class=OpenPlansTestCase,
                                        setUp=base_tt_setup,
                                        globs=locals())
    
    suites = (readme,)
    for suite in suites:
        suite.layer = MockHTTPWithContent
        
    return unittest.TestSuite(suites)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
