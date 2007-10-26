import unittest
from zope.testing import doctest
from Testing import ZopeTestCase as ztc
from opencore.testing.layer import OpencoreContent as test_layer

import warnings; warnings.filterwarnings("ignore")

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

def test_suite():
    from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
    from zope.component import getUtility
                   
    globs = locals()

    readme = ztc.FunctionalDocFileSuite('README.txt',
                                        package='opencore.api',
                                        optionflags=optionflags,
                                        test_class=OpenPlansTestCase,
                                        globs=globs,
                                        )
    readme.layer = test_layer
    
    member_api = ztc.FunctionalDocFileSuite('member_api.txt',
                                            package='opencore.api',
                                            optionflags=optionflags,
                                            test_class=OpenPlansTestCase,
                                            globs=globs,
                                            )
    
    suites = (readme, member_api)
    for suite in suites:
        suite.layer = test_layer
        
    return unittest.TestSuite(suites)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
