import unittest
from Products.CMFCore.utils import getToolByName
from opencore.testing.layer import OpencoreContent
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Products.CMFCore.tests.base.testcase import LogInterceptor
from opencore.content.member import log_subsystem

class TestOpenMember(OpenPlansTestCase, LogInterceptor):

    layer = OpencoreContent
    
    def tearDown(self):
        self._ignore_log_errors(subsystem=log_subsystem)

    def test_validateId(self):
        mdtool = getToolByName(self.portal, 'portal_memberdata')
        mem = mdtool._getOb('m1')
        result = mem.validate_id('m2')
        self.failIf(result is None)

        result = mem.validate_id('(dfsf')
        self.failIf(result is None)

        result = mem.validate_id('AnonYmouse')
        self.failIf(result is None)

        result = mem.validate_id('TopPhat')
        self.failIf(result is None)

    def test_validateEmail(self):
        mdtool = getToolByName(self.portal, 'portal_memberdata')
        mem = mdtool._getOb('m1')

        # duplicate not allowed
        result = mem.validate_email('notreal2@example.com')
        self.failIf(result is None)

        # blacklist is enforced
        result = mem.validate_email('greetings@openplans.org')
        self.failIf(result is None)

    def test_projectBrains(self):
        mdtool = getToolByName(self.portal, 'portal_memberdata')
        mem = mdtool._getOb('m1')
        projbrains = mem.projectBrains()
        titles = [i.Title for i in projbrains]
        self.failIf(set(titles) != set(['Project Two', 'Project Three',
                                        'Project One']))

    def test_member_noConfirmationKey(self):
        mdtool = getToolByName(self.portal, 'portal_memberdata')
        mem = mdtool._getOb('m1')
        code = mem.getUserConfirmationCode()
        self.failUnless(code)
        delattr(mem, '_confirmation_key')
        # When the confirmation key is missing, accessing it will
        # create a new one implicitly, to work around an unknown bug
        # where members get created without one.
        # http://trac.openplans.org/errors-openplans/ticket/49
        #
        # Also, we do some logging. Rather than pollute stdout,
        # we'll use the LogInterceptor mixin to test the log.
        self._catch_log_errors(ignored_level=9999, subsystem=log_subsystem)
        code2 = mem.getUserConfirmationCode()
        self.failUnless(
            self.logged[-1].getMessage(),
            "Member 'm1' didn't have a confirmation code, creating one")
        self.failUnless(code2)
        self.failIf(code2 == code)
        

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestOpenMember))
    return suite
