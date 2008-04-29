import unittest

from Products.CMFCore.utils import getToolByName
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from opencore.browser.topnav.interfaces import ITopnavMenuItems
from opencore.browser.topnav.tests import parse_topnav_context_menu
from opencore.testing.layer import OpencoreContent
from zope.component import getMultiAdapter

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
        self.logout()

        mem_id = self.mem_id = 'm1'
        self.login(mem_id)
        mem = mtool.getMemberById(mem_id)
        mtool.createMemberArea(mem_id)
        self.mf = mtool.getHomeFolder(mem_id)
        self.mhome = self.mf._getOb('m1-home')
        # preserve the orignal URL
        self._orig_actual_url = self.request.ACTUAL_URL 

    def beforeTearDown(self):
        # XXX this may not be necessary, but it's safer just in case
        self.request.ACTUAL_URL = self._orig_actual_url
        self.clearMemoCache()

    def _get_topnav_html(self, context):
        self.clearMemoCache()
        view = getMultiAdapter((context, self.request),
                               name='oc-topnav')
        manager = getMultiAdapter((context, self.request, view),
                                  ITopnavMenuItems,
                                  name='opencore.topnavmenu')
        manager.update()
        return manager.render()
        
    def test_menudata(self):
        # I would love to refactor this into multiple test cases, but
        # frankly, the setup/teardown time makes this unbearable.  So,
        # I'll just comment the different sections...

        # Test to see if the 'Pages' is highlighted.
        self.request.ACTUAL_URL = self.mf.absolute_url()
        html = self._get_topnav_html(context=self.mhome)
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(len(lis), 3)

        self.failIf(lis[0]['selected'])
        self.assertEqual('Profile', links[0]['name'])
        self.assertEqual('%s/profile' % self.mf.absolute_url(),
                         links[0]['href'])
        
        self.assertEqual(lis[1]['selected'], u'oc-topnav-selected')
        self.assertEqual('Pages', links[1]['name'])
        self.assertEqual(self.mhome.absolute_url(),
                         links[1]['href'])
        
        self.failIf(lis[2]['selected'])
        self.assertEqual('Account', links[2]['name'])
        self.assertEqual('%s/account' % self.mf.absolute_url(),
                         links[2]['href'])

        # Test to see if the 'Profile' is highlighted
        profile_url = "%s/profile" % self.mf.absolute_url()
        self.request.ACTUAL_URL = profile_url
        html = self._get_topnav_html(context=self.mf)
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(len(lis), 3)

        self.assertEqual(lis[0]['selected'], u'oc-topnav-selected')
        self.assertEqual('Profile', links[0]['name'])

        self.failIf(lis[1]['selected'])
        self.failIf(lis[2]['selected'])

        # Test to see if 'Account' is highlighted
        userprefs_url = "%s/account" % self.mf.absolute_url()
        self.request.ACTUAL_URL = userprefs_url
        html = self._get_topnav_html(context=self.mf)
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(len(lis), 3)

        self.failIf(lis[0]['selected'])
        self.failIf(lis[1]['selected'])

        self.assertEqual(lis[2]['selected'], u'oc-topnav-selected')
        self.assertEqual('Account', links[2]['name'])

        # Test links when viewing topnav for another user's profile
        # (not the one who's logged in).
        other_profile_url = "%s/profile" % self.other_mf.absolute_url()
        self.request.ACTUAL_URL = other_profile_url
        html = self._get_topnav_html(context=self.other_mf)
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(len(lis), 2)

        self.assertEqual(lis[0]['selected'], u'oc-topnav-selected')
        self.assertEqual('%s/profile' % self.other_mf.absolute_url(),
                         links[0]['href'])

        self.failIf(lis[1]['selected'])
        self.assertEqual('%s/m2-home' % self.other_mf.absolute_url(),
                         links[1]['href'])


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
        self.logout()
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
        # add 'preferences', replace 'team' with link to manage-team, remove 'join'

        self.failUnless(len(menudata) == 4)
        self.assertEqual(mdmap['wiki']['href'], self.proj.absolute_url() + '/project-home')
        self.failUnless(mdmap['wiki']['selected'])
        self.failIf(mdmap['contents']['selected'])
        self.failIf(mdmap['team']['selected'])
        self.failIf(mdmap['preferences']['selected'])
        self.failUnless(mdmap['team']['href'].endswith('manage-team'))

        orig_actual_url = self.request.ACTUAL_URL

        # the 'contents' and 'preferences' views are on the project
        # object itself, not the project home page
        self.clearMemoCache()
        contents_url = "%s/contents" % self.proj.absolute_url()
        self.request.ACTUAL_URL = contents_url
        menudata = self.proj_view.menudata
        mdmap = self.make_menudata_map(menudata)
        self.failUnless(len(menudata) == 4)
        self.assertEqual(mdmap['wiki']['href'], self.proj.absolute_url() + '/project-home')
        self.failIf(mdmap['wiki']['selected'])
        self.failUnless(mdmap['contents']['selected'])
        self.failIf(mdmap['team']['selected'])
        self.failIf(mdmap['preferences']['selected'])
        
        self.clearMemoCache()
        team_url = "%s/team" % self.proj.absolute_url()
        self.request.ACTUAL_URL = team_url
        menudata = self.proj_view.menudata
        mdmap = self.make_menudata_map(menudata)
        self.failUnless(len(menudata) == 4)
        self.assertEqual(menudata[0]['href'], self.proj.absolute_url() + '/project-home')
        self.failIf(mdmap['wiki']['selected'])
        self.failIf(mdmap['contents']['selected'])
        self.failUnless(mdmap['team']['selected'])
        self.failIf(mdmap['preferences']['selected'])

        self.clearMemoCache()
        manage_url = "%s/manage-team" % self.proj.absolute_url()
        self.request.ACTUAL_URL = manage_url
        menudata = self.proj_view.menudata
        mdmap = self.make_menudata_map(menudata)
        self.failUnless(len(menudata) == 4)
        self.assertEqual(menudata[0]['href'], self.proj.absolute_url() + '/project-home')
        self.failIf(mdmap['wiki']['selected'])
        self.failIf(mdmap['contents']['selected'])
        self.failUnless(mdmap['team']['selected'])
        self.failIf(mdmap['preferences']['selected'])

        self.clearMemoCache()
        prefs_url = "%s/preferences" % self.proj.absolute_url()
        self.request.ACTUAL_URL = prefs_url
        menudata = self.proj_view.menudata
        mdmap = self.make_menudata_map(menudata)
        self.failUnless(len(menudata) == 4)
        self.assertEqual(mdmap['wiki']['href'], self.proj.absolute_url() + '/project-home')
        self.failIf(mdmap['wiki']['selected'])
        self.failIf(mdmap['contents']['selected'])
        self.failIf(mdmap['team']['selected'])
        self.failUnless(mdmap['preferences']['selected'])

        self.request.ACTUAL_URL = orig_actual_url


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMemberMenu))
    suite.addTest(unittest.makeSuite(TestProjectMenu))
    return suite
