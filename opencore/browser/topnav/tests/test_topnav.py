import os, sys
import unittest

from zope.interface import alsoProvides
from zope.component import getMultiAdapter

from Products.CMFCore.utils import getToolByName

from opencore.browser.topnav.tests import parse_topnav_context_menu
from opencore.testing.layer import OpencoreContent
from opencore.interfaces.member import IMemberFolder
from opencore.project.utils import project_noun
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase, \
     makeContent

class TestTopNav(OpenPlansTestCase):

    layer = OpencoreContent

    def afterSetUp(self):
        OpenPlansTestCase.afterSetUp(self)
        self.request = self.portal.REQUEST
        mtool = getToolByName(self.portal, 'portal_membership')
        mtool.createMemberArea('m1')
        self.memhome = memhome = self.portal.people.m1
        alsoProvides(memhome, IMemberFolder)

    def test_usermenu(self):
        req = self.request
        req.ACTUAL_URL += '/plone/people/m1/profile'
        self.login('m1')
        topnav = getMultiAdapter((self.memhome, req), name='oc-topnav')
        html = topnav.contextmenu
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(3, len(lis))
        self.assertEqual('oc-topnav-selected', lis[0]['selected'])
        self.assertEqual(False, lis[1]['selected'])
        self.assertEqual(False, lis[2]['selected'])
        self.assertEqual(u'Profile', links[0]['name'])
        self.assertEqual(u'Pages', links[1]['name'])
        self.assertEqual(u'Account', links[2]['name'])

        self.clearMemoCache()
        self.logout()
        topnav = getMultiAdapter((self.memhome, req), name='oc-topnav')
        html = topnav.contextmenu
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(2, len(lis))
        self.assertEqual(u'oc-topnav-selected', lis[0]['selected'])
        self.assertEqual(False, lis[1]['selected'])
        self.assertEqual(u'Profile', links[0]['name'])
        self.assertEqual(u'Pages', links[1]['name'])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTopNav))
    return suite
