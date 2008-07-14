import unittest
from Products.CMFCore.utils import getToolByName
from opencore.testing.layer import OpencoreContent
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase

class TestOpenMember(OpenPlansTestCase):

    layer = OpencoreContent

    def test_validateId(self):
        mdtool = getToolByName(self.portal, 'portal_memberdata')
        mem = mdtool._getOb('m1')
        result = mem.validate_id('m2')
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
        

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestOpenMember))
    return suite
