import os, sys
import unittest

from plone.memoize.view import ViewMemo
from zope.app.annotation.interfaces import IAnnotations
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

        other_mem_id = self.mem_id = 'm2'
        self.login(other_mem_id)
        other_mem = mtool.getMemberById(other_mem_id)
        mtool.createMemberArea(other_mem_id)
        self.other_mf = mtool.getHomeFolder(other_mem_id)
        self.other_mhome = self.other_mf._getOb(self.other_mf.getDefaultPage())
        self.other_view = getMultiAdapter((self.other_mhome, self.request),
                                          name='topnav-member-menu')
        self.logout()

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

        self.clearMemoCache()
        other_profile_url = "%s/profile" % self.other_mf.absolute_url()
        self.request.ACTUAL_URL = other_profile_url
        menudata = self.other_view.menudata
        self.failUnless(len(menudata) == 2)
        self.assertEqual(self.other_mf.absolute_url(), menudata[0]['href'])
        self.failIf(menudata[0]['selected'])
        self.failUnless(menudata[1]['selected'])

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
        request = self.request
        request.ACTUAL_URL = self.request.URL = 'http://nohost/plone/projects/p3/project-home'
        self.proj_view = getMultiAdapter((self.proj, self.request),
                                          name='topnav-project-menu')
        self.proj_home = self.proj._getOb(self.proj.getDefaultPage())
        self.phome_view = getMultiAdapter((self.proj_home, self.request),
                                          name='topnav-project-menu')

    def make_menudata_map(self, menudata):
        mdmap = dict()
        for i in menudata:
            key = i['content'].lower()
            mdmap[key] = i
        return mdmap

    def test_menudata(self):
        menudata = self.phome_view.menudata
        mdmap = self.make_menudata_map(menudata)
        # 'wiki', 'contents', 'team', and 'join project'

        self.failUnless(len(menudata) == 4)
        self.assertEqual(mdmap['wiki']['href'], self.proj.absolute_url() + '/project-home')
        self.failUnless(mdmap['wiki']['selected'])
        self.failIf(mdmap['contents']['selected'])
        self.failIf(mdmap['team']['selected'])
        self.failIf(mdmap['join project']['selected'])

        self.clearMemoCache()
        self.clearInstanceCache(self.phome_view)
        self.login(self.proj_admin_id)
        menudata = self.phome_view.menudata
        mdmap = self.make_menudata_map(menudata)
        # add 'preferences' and 'manage team', remove 'join'

        self.failUnless(len(menudata) == 5)
        self.assertEqual(mdmap['wiki']['href'], self.proj.absolute_url() + '/project-home')
        self.failUnless(mdmap['wiki']['selected'])
        self.failIf(mdmap['contents']['selected'])
        self.failIf(mdmap['team']['selected'])
        self.failIf(mdmap['manage team']['selected'])
        self.failIf(mdmap['preferences']['selected'])
        self.failUnless(mdmap.has_key('manage team'))

        orig_actual_url = self.request.ACTUAL_URL

        # the 'contents' and 'preferences' views are on the project
        # object itself, not the project home page
        self.clearMemoCache()
        contents_url = "%s/contents" % self.proj.absolute_url()
        self.request.ACTUAL_URL = contents_url
        menudata = self.proj_view.menudata
        mdmap = self.make_menudata_map(menudata)
        self.failUnless(len(menudata) == 5)
        self.assertEqual(mdmap['wiki']['href'], self.proj.absolute_url() + '/project-home')
        self.failIf(mdmap['wiki']['selected'])
        self.failUnless(mdmap['contents']['selected'])
        self.failIf(mdmap['team']['selected'])
        self.failIf(mdmap['manage team']['selected'])
        self.failIf(mdmap['preferences']['selected'])
        
        self.clearMemoCache()
        team_url = "%s/team" % self.proj.absolute_url()
        self.request.ACTUAL_URL = team_url
        menudata = self.proj_view.menudata
        mdmap = self.make_menudata_map(menudata)
        self.failUnless(len(menudata) == 5)
        self.assertEqual(menudata[0]['href'], self.proj.absolute_url() + '/project-home')
        self.failIf(mdmap['wiki']['selected'])
        self.failIf(mdmap['contents']['selected'])
        self.failUnless(mdmap['team']['selected'])
        self.failIf(mdmap['manage team']['selected'])
        self.failIf(mdmap['preferences']['selected'])

        self.clearMemoCache()
        manage_url = "%s/manage-team" % self.proj.absolute_url()
        self.request.ACTUAL_URL = manage_url
        menudata = self.proj_view.menudata
        mdmap = self.make_menudata_map(menudata)
        self.failUnless(len(menudata) == 5)
        self.assertEqual(menudata[0]['href'], self.proj.absolute_url() + '/project-home')
        self.failIf(mdmap['wiki']['selected'])
        self.failIf(mdmap['contents']['selected'])
        self.failIf(mdmap['team']['selected'])
        self.failUnless(mdmap['manage team']['selected'])
        self.failIf(mdmap['preferences']['selected'])

        self.clearMemoCache()
        prefs_url = "%s/preferences" % self.proj.absolute_url()
        self.request.ACTUAL_URL = prefs_url
        menudata = self.proj_view.menudata
        mdmap = self.make_menudata_map(menudata)
        self.failUnless(len(menudata) == 5)
        self.assertEqual(mdmap['wiki']['href'], self.proj.absolute_url() + '/project-home')
        self.failIf(mdmap['wiki']['selected'])
        self.failIf(mdmap['contents']['selected'])
        self.failIf(mdmap['team']['selected'])
        self.failIf(mdmap['manage team']['selected'])
        self.failUnless(mdmap['preferences']['selected'])

        self.request.ACTUAL_URL = orig_actual_url


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMemberMenu))
    suite.addTest(unittest.makeSuite(TestProjectMenu))
    return suite
