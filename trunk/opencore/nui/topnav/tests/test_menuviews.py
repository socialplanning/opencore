import os, sys
import unittest

from plone.memoize.view import ViewMemo
from zope.annotation.interfaces import IAnnotations
from zope.interface import alsoProvides
from zope.component import getMultiAdapter

from Products.CMFCore.utils import getToolByName

from opencore.testing.layer import OpencoreContent
from opencore.siteui.interfaces import IMemberFolder

from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase


class TestMemberMenu(OpenPlansTestCase):

    layer = OpencoreContent

    def afterSetUp(self):
        OpenPlansTestCase.afterSetUp(self)
        self.request = self.portal.REQUEST
        mtool = getToolByName(self.portal, 'portal_membership')
        mem_id = self.mem_id = 'm1'
        self.login(mem_id)
        mem = mtool.getMemberById(mem_id)
        mtool.createMemberArea(mem_id)
        self.mf = mtool.getHomeFolder(mem_id)
        self.mhome = self.mf._getOb(self.mf.getDefaultPage())
        self.view = getMultiAdapter((self.mhome, self.request),
                                    name='topnav-member-menu')
        
    def test_menudata(self):
        menudata = self.view.menudata
        self.failUnless(len(menudata) == 3)
        self.assertEqual(self.mf.absolute_url(), menudata[0]['href'])
        self.failUnless(menudata[0]['selected'])
        self.failIf(menudata[1]['selected'])
        self.failIf(menudata[2]['selected'])

        orig_actual_url = self.request.ACTUAL_URL

        self.clearMemoCache()
        profile_url = "%s/profile" % self.mf.absolute_url()
        self.request.ACTUAL_URL = profile_url
        menudata = self.view.menudata
        self.failUnless(len(menudata) == 3)
        self.assertEqual(self.mf.absolute_url(), menudata[0]['href'])
        self.failIf(menudata[0]['selected'])
        self.failUnless(menudata[1]['selected'])
        self.failIf(menudata[2]['selected'])

        self.clearMemoCache()
        userprefs_url = "%s/account" % self.mf.absolute_url()
        self.request.ACTUAL_URL = userprefs_url
        menudata = self.view.menudata
        self.failUnless(len(menudata) == 3)
        self.assertEqual(self.mf.absolute_url(), menudata[0]['href'])
        self.failIf(menudata[0]['selected'])
        self.failIf(menudata[1]['selected'])
        self.failUnless(menudata[2]['selected'])

        # XXX this may not be necessary, but it's safer just in case
        self.request.ACTUAL_URL = orig_actual_url


class TestProjectMenu(OpenPlansTestCase):

    layer = OpencoreContent

    def afterSetUp(self):
        OpenPlansTestCase.afterSetUp(self)
        self.request = self.portal.REQUEST
        self.proj_id = 'p3'
        self.proj_admin_id = 'm1'
        self.proj = self.portal.projects._getOb(self.proj_id)
        self.proj_view = getMultiAdapter((self.proj, self.request),
                                          name='topnav-project-menu')
        self.proj_home = self.proj._getOb(self.proj.getDefaultPage())
        self.phome_view = getMultiAdapter((self.proj_home, self.request),
                                          name='topnav-project-menu')

    def test_menudata(self):
        menudata = self.phome_view.menudata
        # 'home', 'contents', 'team', and 'join project'
        self.failUnless(len(menudata) == 4)
        self.assertEqual(menudata[0]['href'], self.proj.absolute_url())
        self.failUnless(menudata[0]['selected'])
        self.failIf(menudata[1]['selected'])
        self.failIf(menudata[2]['selected'])
        self.failIf(menudata[3]['selected'])

        self.clearMemoCache()
        self.clearInstanceCache(self.phome_view)
        self.login(self.proj_admin_id)
        menudata = self.phome_view.menudata
        # add 'account' and 'manage team', remove 'join'
        self.failUnless(len(menudata) == 5)
        self.assertEqual(menudata[0]['href'], self.proj.absolute_url())
        self.failUnless(menudata[0]['selected'])
        self.failIf(menudata[1]['selected'])
        self.failIf(menudata[2]['selected'])
        self.failIf(menudata[3]['selected'])
        self.failIf(menudata[4]['selected'])
        self.failUnless(menudata[4]['content'] == 'Manage team')

        orig_actual_url = self.request.ACTUAL_URL

        # the 'contents' and 'account' views are on the project
        # object itself, not the project home page
        self.clearMemoCache()
        contents_url = "%s/contents" % self.proj.absolute_url()
        self.request.ACTUAL_URL = contents_url
        menudata = self.proj_view.menudata
        self.failUnless(len(menudata) == 5)
        self.assertEqual(menudata[0]['href'], self.proj.absolute_url())
        self.failIf(menudata[0]['selected'])
        self.failUnless(menudata[1]['selected'])
        self.failIf(menudata[2]['selected'])
        self.failIf(menudata[3]['selected'])
        self.failIf(menudata[4]['selected'])
        
        self.clearMemoCache()
        team_url = "%s/team" % self.proj.absolute_url()
        self.request.ACTUAL_URL = team_url
        menudata = self.proj_view.menudata
        self.failUnless(len(menudata) == 5)
        self.assertEqual(menudata[0]['href'], self.proj.absolute_url())
        self.failIf(menudata[0]['selected'])
        self.failIf(menudata[1]['selected'])
        self.failUnless(menudata[2]['selected'])
        self.failIf(menudata[3]['selected'])
        self.failIf(menudata[4]['selected'])

        self.clearMemoCache()
        prefs_url = "%s/preferences" % self.proj.absolute_url()
        self.request.ACTUAL_URL = prefs_url
        menudata = self.proj_view.menudata
        self.failUnless(len(menudata) == 5)
        self.assertEqual(menudata[0]['href'], self.proj.absolute_url())
        self.failIf(menudata[0]['selected'])
        self.failIf(menudata[1]['selected'])
        self.failIf(menudata[2]['selected'])
        self.failUnless(menudata[3]['selected'])
        self.failIf(menudata[4]['selected'])

        self.clearMemoCache()
        manage_url = "%s/manage-team" % self.proj.absolute_url()
        self.request.ACTUAL_URL = manage_url
        menudata = self.proj_view.menudata
        self.failUnless(len(menudata) == 5)
        self.assertEqual(menudata[0]['href'], self.proj.absolute_url())
        self.failIf(menudata[0]['selected'])
        self.failIf(menudata[1]['selected'])
        self.failIf(menudata[2]['selected'])
        self.failIf(menudata[3]['selected'])
        self.failUnless(menudata[4]['selected'])

        self.request.ACTUAL_URL = orig_actual_url


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMemberMenu))
    suite.addTest(unittest.makeSuite(TestProjectMenu))
    return suite
