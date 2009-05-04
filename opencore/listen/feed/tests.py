# This subpackage depends on opencore.feed, so don't run the tests if it's not
# installed...
try:
    __import__('opencore.feed')
    from opencore.feed.base import BaseFeedAdapter
    run_tests = True
except ImportError:
    run_tests = False

import doctest
import unittest

if run_tests:
    # XXX HARDCODED DOMAIN
    BaseFeedAdapter.memberURL = lambda x, y: 'http://www.openplans.org'

class DummyContext(object):
    def Title(self):
        return 'Dummy title'
    def Description(self):
        return 'Dummy description'
    def absolute_url(self):
        return 'http://dummy/context/url'
    def getPhysicalPath(self):
        return ['dummy', 'context', 'url']
    def modified(self):
        from datetime import datetime
        return datetime.now()
    def Creator(self):
        return 'Dummy creator'

def test_suite():
    listen_suite = doctest.DocFileSuite('listen.txt',
                                      optionflags=doctest.ELLIPSIS)

    if run_tests:
        return unittest.TestSuite((listen_suite,))
    return unittest.TestSuite()


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
