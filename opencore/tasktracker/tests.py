import os, sys, unittest
from zope.testing import doctest
from collective.testing.layer import ZCMLLayer
from collective.testing import utils
from zope.testing import doctestunit
from zope.testing import doctest
from zope.component import testing
from Testing import ZopeTestCase as ztc
from Products.Five import zcml
from zope.interface import alsoProvides

import warnings; warnings.filterwarnings("ignore")

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

def readme_setup(tc):
    tc.new_request = utils.new_request()
    import opencore.tasktracker
    from zope.app.annotation.interfaces import IAttributeAnnotatable
    from zope.testing.loggingsupport import InstalledHandler
    zcml.load_config('test.zcml', opencore.tasktracker)
    tc.new_request._hacked_path=None
    tc.log = InstalledHandler(opencore.tasktracker.LOG)

def directive_setup(tc):
    import opencore.tasktracker
    zcml.load_config('test-directive.zcml', opencore.tasktracker)

def test_suite():
    from zope.component import getMultiAdapter, getUtility
    from zope.interface import alsoProvides
##     readme = ztc.FunctionalDocFileSuite('README.txt',
##                                         package='opencore.tasktracker',
##                                         optionflags=optionflags,
##                                         setUp=readme_setup,
##                                         globs=locals())
    
##     suites = (readme,)
##     for suite in suites:
##         suite.layer = ZCMLLayer
    directive = doctest.DocFileSuite('directive.txt',
                                     package='opencore.tasktracker',
                                     optionflags=optionflags,
                                     setUp=directive_setup,
                                     globs=locals())
    suites = (directive,)
    return unittest.TestSuite(suites)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
