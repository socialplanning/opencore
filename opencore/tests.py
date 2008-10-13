import unittest

class Storage(object):
    pass

class TestUtils(unittest.TestCase):

    def test_timestamp_memoize(self):
        from opencore.utils import timestamp_memoize
        s = Storage()

        @timestamp_memoize(1, s)
        def doubler(val):
            return val + val

        self.assertEqual(10, doubler(5))
        self.assertEqual(10, doubler(10))

        @timestamp_memoize(0, s)
        def doubler(val):
            return val + val

        self.assertEqual(10, doubler(5))
        self.assertEqual(20, doubler(10))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUtils))
    return suite
