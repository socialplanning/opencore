import os, sys
import unittest

from zope.interface import alsoProvides
from zope.component import getMultiAdapter

from Products.CMFCore.utils import getToolByName

from opencore.testing.layer import OpencoreContent
from opencore.siteui.interfaces import IMemberFolder

from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase, \
     makeContent


class TestTopNav(OpenPlansTestCase):

    layer = OpencoreContent

    def afterSetUp(self):
        OpenPlansTestCase.afterSetUp(self)
        self.request = self.portal.REQUEST

    def test_contextmenu(self):
        req = self.request
        topnav = getMultiAdapter((self.portal, req), name='oc-topnav')
        self.assertEqual(topnav.contextmenu.name,
                         'topnav-default-menu')

        self.clearMemoCache()
        proj = self.portal.projects.p1
        topnav = getMultiAdapter((proj, req), name='oc-topnav')
        self.assertEqual(topnav.contextmenu.name,
                         'topnav-project-menu')

        self.clearMemoCache()
        mtool = getToolByName(self.portal, 'portal_membership')
        mtool.createMemberArea('m1')
        memhome = self.portal.people.m1
        alsoProvides(memhome, IMemberFolder)
        topnav = getMultiAdapter((memhome, req), name='oc-topnav')
        self.assertEqual(topnav.contextmenu.name,
                         'topnav-member-menu')
        
    def test_usermenu(self):
        req = self.request
        self.login('m1')
        topnav = getMultiAdapter((self.portal, req), name='oc-topnav')
        self.assertEqual(topnav.usermenu.name,
                         'topnav-auth-user-menu')

        self.clearMemoCache()
        self.logout()
        topnav = getMultiAdapter((self.portal, req), name='oc-topnav')
        self.assertEqual(topnav.usermenu.name,
                         'topnav-anon-user-menu')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTopNav))
    return suite
