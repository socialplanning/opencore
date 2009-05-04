from opencore.feed.base import BaseFeedAdapter
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import SiteSetupLayer
import doctest
import unittest

# XXX Monkeypatching should be scoped to just the test it's needed for,
# and restored on teardown; but for some reason I can't make that work.
# XXX HARDCODED DOMAIN
BaseFeedAdapter.memberURL = lambda x, y: 'http://www.openplans.org'
BaseFeedAdapter.member_portraitURL = lambda x, y: 'http://www.openplans.org/++resource++img/topp_logo.jpg'


    
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
