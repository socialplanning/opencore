import os, sys
import unittest

from plone.memoize.view import ViewMemo
from zope.annotation.interfaces import IAnnotations
from zope.interface import alsoProvides

from Products.CMFCore.utils import getToolByName

from opencore.testing.layer import OpencoreContent
from opencore.siteui.interfaces import IMemberFolder

from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase, \
     makeContent


class TestTopNav(OpenPlansTestCase):

    layer = OpencoreContent

    def clearMemoCache(self):
        req = self.portal.REQUEST
        annotations = IAnnotations(req)
        cache = annotations.get(ViewMemo.key, None)
        if cache is not None:
            annotations[ViewMemo.key] = dict()

    def test_contextmenu(self):
        topnav = self.portal.unrestrictedTraverse('oc-topnav')
        self.assertEqual(topnav.contextmenu.name,
                         'topnav-default-menu')

        self.clearMemoCache()
        proj = self.portal.projects.p1
        topnav = proj.unrestrictedTraverse('oc-topnav')
        self.assertEqual(topnav.contextmenu.name,
                         'topnav-project-menu')

        self.clearMemoCache()
        mtool = getToolByName(self.portal, 'portal_membership')
        mtool.createMemberArea('m1')
        memhome = self.portal.people.m1
        alsoProvides(memhome, IMemberFolder)
        topnav = memhome.unrestrictedTraverse('oc-topnav')
        self.assertEqual(topnav.contextmenu.name,
                         'topnav-member-menu')
        

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTopNav))
    return suite
