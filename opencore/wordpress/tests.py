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

def clean_CA(tc):
    return cleanUp()

import warnings; warnings.filterwarnings("ignore")

optionflags = doctest.ELLIPSIS

def readme_setup(tc):
    tc.new_request = utils.new_request()
    import opencore.wordpress
    from zope.app.annotation.interfaces import IAttributeAnnotatable
    from zope.testing.loggingsupport import InstalledHandler
    tc.log = InstalledHandler(opencore.wordpress.LOG)
    setSite(tc.app.plone)

def test_suite():
    from zope.component import getMultiAdapter, getUtility
    from opencore.testing import * # star imports are for pansies
    from opencore.utility.interfaces import IHTTPClient
    
    readme = ztc.FunctionalDocFileSuite('README.txt',
                                        package='opencore.wordpress',
                                        optionflags=optionflags,
                                        setUp=readme_setup,
                                        globs=locals())
    
    suites = (readme,)
    for suite in suites:
        suite.layer = MockHTTPWithContent
        
    return unittest.TestSuite(suites)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
