import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Testing.ZopeTestCase import FunctionalDocFileSuite
from opencore.testing.layer import OpencoreContent

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

    setup.setupPloneSite()
    def readme_setup(tc):
        tc._refreshSkinData()

    globs = locals()
    readme = FunctionalDocFileSuite("README.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui.wiki',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=readme_setup
                                    )
    
    wikiadd = FunctionalDocFileSuite("add.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui.wiki',
                                    test_class=FunctionalTestCase,
                                    globs = globs
                                    )

    htmldiff2 = doctest.DocFileSuite('test_htmldiff2.txt')
    readme.layer = OpencoreContent
    wikiadd.layer = OpencoreContent

    return unittest.TestSuite((wikiadd, readme, htmldiff2))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
