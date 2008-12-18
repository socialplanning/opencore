import unittest

class TestUtils(unittest.TestCase):

    def test_timestamp_memoize(self):
        from opencore.utils import timestamp_memoize

        @timestamp_memoize(1)
        def doubler(val):
            return val + val

        self.assertEqual(10, doubler(5))
        self.assertEqual(10, doubler(10))

        @timestamp_memoize(0)
        def doubler(val):
            return val + val

        self.assertEqual(10, doubler(5))
        self.assertEqual(20, doubler(10))



    def test_member_title__dict(self):
        from opencore.utils import member_title
        self.assertEqual(member_title({'fullname': 'NAME', 'id': 'ID'}),
                         'NAME')
        self.assertEqual(member_title({'fullname': '', 'id': 'ID'}), 
                         'ID')
        self.assertRaises(KeyError, 
                          member_title, {'fullname': ''})
        self.assertRaises(KeyError, 
                          member_title, {'id': 'ID'})
        self.assertRaises(KeyError, 
                          member_title, {})

        
    def test_member_title__wrongtype(self):
        from opencore.utils import member_title
        self.assertRaises(TypeError, member_title, 1)
        self.assertRaises(TypeError, member_title, object())
        self.assertRaises(TypeError, member_title, None)

#     def test_member_title__string(self):
#         # XXX this one would need to be run in a layer with more site setup,
#         # or a ton of mocking.
#         pass


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestUtils))
    return suite
