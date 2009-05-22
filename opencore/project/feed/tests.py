from opencore.testing import dtfactory as dtf
from opencore.testing.layer import SiteSetupLayer
import doctest
import unittest

    
def test_suite():
    project_suite = doctest.DocFileSuite('project.txt',
                                         optionflags=doctest.ELLIPSIS)
    page_suite = dtf.ZopeDocFileSuite("page.txt",
                                      package='opencore.project.feed',
                                      globs = globals(),
                                      layer=SiteSetupLayer,
                                      )
    return unittest.TestSuite((project_suite,
                               page_suite,
                               ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
