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
from opencore.testing.layer import SiteSetupLayer, OpenCoreContent

import warnings; warnings.filterwarnings("ignore")

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

def test_suite():
    from zope.component import getMultiAdapter, getUtility
    from zope.interface import alsoProvides
    from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase

    readme = ztc.FunctionalDocFileSuite('README.txt',
                                        package='opencore.api',
                                        optionflags=optionflags,
                                        test_class=OpenPlansTestCase,
                                        globs=locals(),
                                        )
    member_api = ztc.FunctionalDocFileSuite('member_api.txt',
                                            package='opencore.api',
                                            optionflags=optionflags,
                                            test_class=OpenPlansTestCase,
                                            globs=locals(),
                                            )
    
    zcml_suites = (readme,member_api)
    for suite in zcml_suites:
        suite.layer = OpenCoreContent
        
    suites = zcml_suites
    return unittest.TestSuite(suites)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
