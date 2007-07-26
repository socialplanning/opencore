import os, sys, unittest
from zope.testing import doctest
from collective.testing import utils
from zope.testing import doctestunit
from zope.testing import doctest
from zope.component import testing
from Testing import ZopeTestCase as ztc
from Products.Five import zcml
from zope.interface import alsoProvides
from zope.testing.cleanup import cleanUp
#from opencore.testing.layer import SiteSetupLayer, OpenCoreContent, ZCML
from collective.testing.layer import ZCMLLayer as ZCML

import warnings; warnings.filterwarnings("ignore")

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

def test_suite():
    from zope.component import getMultiAdapter, getUtility
    from opencore.testing import *
    import pdb; st = pdb.set_trace
    readme = ztc.FunctionalDocFileSuite('README.txt',
                                        package='opencore.utility',
                                        optionflags=optionflags,
                                        globs=locals())
    
    zcml_suites = (readme,)
    for suite in zcml_suites:
        suite.layer = ZCML
        
    suites = zcml_suites
    return unittest.TestSuite(suites)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
