import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Testing.ZopeTestCase import FunctionalDocFileSuite
from opencore.testing.layer import OpencoreContent
from opencore.testing import dtfactory as dtf

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
    import pdb
    
    setup.setupPloneSite()
    def readme_setup(tc):
        tc._refreshSkinData()

    page_id = 'project-home'
    globs = locals()
    readme = dtf.ZopeDocFileSuite("README.txt",
                                  optionflags=optionflags,
                                  package='opencore.nui.wiki',
                                  test_class=FunctionalTestCase,
                                  globs = globs,
                                  setUp=readme_setup,
                                  layer = OpencoreContent
                                  )
    
    wikiadd = dtf.ZopeDocFileSuite("add.txt",
                                   optionflags=optionflags,
                                   package='opencore.nui.wiki',
                                   test_class=FunctionalTestCase,
                                   globs = globs,
                                   layer = OpencoreContent
                                   )

    history = dtf.ZopeDocFileSuite("history.txt",
                                   optionflags=optionflags,
                                   package='opencore.nui.wiki',
                                   test_class=FunctionalTestCase,
                                   setUp=readme_setup,
                                   globs = globs,
                                   layer = OpencoreContent
                                   )

    htmldiff2 = doctest.DocFileSuite('test_htmldiff2.txt')

    return unittest.TestSuite((wikiadd, readme, history, htmldiff2))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
