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
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from opencore.testing.layer import OpencoreContent as test_layer

import warnings; warnings.filterwarnings("ignore")

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

def test_suite():
    from zope.component import getMultiAdapter, getUtility
    from Products.CMFCore.utils import getToolByName
    from opencore.testing import *
    import pdb; st = pdb.set_trace
    readme = ztc.FunctionalDocFileSuite('README.txt',
                                        package='opencore.utility',
                                        optionflags=optionflags,
                                        globs=locals())
    
    zcml_suites = (readme,)
    for suite in zcml_suites:
        suite.layer = ZCML
    
    email_sender = ztc.FunctionalDocFileSuite("email-sender.txt",
                                              optionflags=optionflags,
                                              package='opencore.utility',
                                              test_class=OpenPlansTestCase,
                                              globs = locals()
                                              )
    email_sender.layer = test_layer
    
    suites = zcml_suites
    return unittest.TestSuite(suites + (email_sender,))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
