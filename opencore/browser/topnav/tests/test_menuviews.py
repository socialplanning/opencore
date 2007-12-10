import os, sys, re
import unittest

from plone.memoize.view import ViewMemo
from zope.app.annotation.interfaces import IAnnotations
from zope.interface import alsoProvides
from zope.component import getMultiAdapter

from Products.CMFCore.utils import getToolByName

from opencore.testing.layer import OpencoreContent
from opencore.interfaces.member import IMemberFolder
from opencore.browser.topnav.interfaces import ITopnavMenuItems

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
        self.logout()

        mem_id = self.mem_id = 'm1'
        self.login(mem_id)
        mem = mtool.getMemberById(mem_id)
        mtool.createMemberArea(mem_id)
        self.mf = mtool.getHomeFolder(mem_id)
        self.mhome = self.mf._getOb(self.mf.getDefaultPage())

    def test_menudata(self):
        # preserve the orignal URL
        orig_actual_url = self.request.ACTUAL_URL 

        # test to see if the 'Wiki' is highlighted
        self.clearMemoCache()
        self.request.ACTUAL_URL = self.mf.absolute_url()
        view = getMultiAdapter(
            (self.mhome, self.request),
            name='oc-topnav')
        manager = getMultiAdapter((self.mhome, self.request, view),
                                  ITopnavMenuItems,
                                  name='opencore.topnavmenu')
        manager.update()
        html = manager.render()
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(len(lis), 3)
        self.assertEqual('%s/m1-home' % self.mf.absolute_url(),
                         links[0]['href'])
        self.assertEqual(lis[0]['selected'], u'oc-topnav-selected')
        self.failIf(lis[1]['selected'])
        self.failIf(lis[2]['selected'])

        # test to see if the 'Profile' is highlighted
        self.clearMemoCache()
        profile_url = "%s/profile" % self.mf.absolute_url()
        self.request.ACTUAL_URL = profile_url
        view = getMultiAdapter((self.mf, self.request),
                               name='oc-topnav')
        manager = getMultiAdapter((self.mf, self.request, view),
                                  ITopnavMenuItems,
                                  name='opencore.topnavmenu')
        manager.update()
        html = manager.render()
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(len(lis), 3)
        self.assertEqual('%s/m1-home' % self.mf.absolute_url(),
                         links[0]['href'])
        self.failIf(lis[0]['selected'])
        self.assertEqual(lis[1]['selected'], u'oc-topnav-selected')
        self.failIf(lis[2]['selected'])

        # test to see if 'Account' is highlighted
        self.clearMemoCache()
        userprefs_url = "%s/account" % self.mf.absolute_url()
        self.request.ACTUAL_URL = userprefs_url
        manager = getMultiAdapter((self.mf, self.request, view),
                                  ITopnavMenuItems,
                                  name='opencore.topnavmenu')
        manager.update()
        html = manager.render()
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(len(lis), 3)
        self.assertEqual('%s/m1-home' % self.mf.absolute_url(),
                         links[0]['href'])
        self.failIf(lis[0]['selected'])
        self.failIf(lis[1]['selected'])
        self.assertEqual(lis[2]['selected'], u'oc-topnav-selected')

        self.clearMemoCache()
        other_profile_url = "%s/profile" % self.other_mf.absolute_url()
        self.request.ACTUAL_URL = other_profile_url
        view = getMultiAdapter((self.other_mf, self.request),
                               name='oc-topnav')
        manager = getMultiAdapter((self.other_mf, self.request, view),
                                  ITopnavMenuItems,
                                  name='opencore.topnavmenu')
        manager.update()
        html = manager.render()
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(len(lis), 2)
        self.assertEqual('%s/m2-home' % self.other_mf.absolute_url(),
                         links[0]['href'])
        self.failIf(lis[0]['selected'])
        self.assertEqual(lis[1]['selected'], u'oc-topnav-selected')

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
        self.proj_home = self.proj._getOb('project-home')
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
