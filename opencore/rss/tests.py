import doctest
import unittest

def test_suite():
    suite = doctest.DocFileSuite('base.txt', optionflags=doctest.ELLIPSIS)
    return unittest.TestSuite((suite,))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
