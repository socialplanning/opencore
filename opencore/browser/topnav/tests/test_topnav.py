import os, sys
import unittest

from zope.interface import alsoProvides
from zope.component import getMultiAdapter

from Products.CMFCore.utils import getToolByName

from opencore.browser.topnav.tests import parse_topnav_context_menu
from opencore.testing.layer import OpencoreContent
from opencore.interfaces.member import IMemberFolder

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
        html = topnav.contextmenu
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(3, len(lis))
        for li in lis:
            self.assertEqual(False, li['selected'])
        people, projects, start = [l['name'] for l in links]
        self.assertEqual(people, u'People')
        self.assertEqual(projects, u'Projects')
        self.assertEqual(start, u'Start A Project')

        self.clearMemoCache()
        proj = self.portal.projects.p1
        topnav = getMultiAdapter((proj, req), name='oc-topnav')
        html = topnav.contextmenu
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(5, len(lis))
        for li in lis[:4]:
            self.assertEqual(False, li['selected'])
        self.assertEqual(u'oc-topnav-join', lis[4]['selected'])
        wiki, lists, team, contents, join = [l['name'] for l in links]
        self.assertEqual(wiki, u'Wiki')
        self.assertEqual(lists, u'Mailing Lists')
        self.assertEqual(team, u'Team')
        self.assertEqual(contents, u'Contents')
        self.assertEqual(join, u'Join Project')

        self.clearMemoCache()
        mtool = getToolByName(self.portal, 'portal_membership')
        mtool.createMemberArea('m1')
        memhome = self.portal.people.m1
        alsoProvides(memhome, IMemberFolder)
        topnav = getMultiAdapter((memhome, req), name='oc-topnav')
        html = topnav.contextmenu
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(2, len(lis))
        self.assertEqual(False, lis[0]['selected'])
        self.assertEqual(False, lis[1]['selected'])
        self.assertEqual(u'Wiki', links[0]['name'])
        self.assertEqual(u'Profile', links[1]['name'])

        # test switch to project context with
        # X-OpenPlans-Project header set
        self.clearMemoCache()
        req.environ['X_OPENPLANS_PROJECT'] = 'p1'
        topnav = getMultiAdapter((self.portal, req), name='oc-topnav')
        html = topnav.contextmenu
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(5, len(lis))
        for li in lis[:4]:
            self.assertEqual(False, li['selected'])
        self.assertEqual(u'oc-topnav-join', lis[4]['selected'])
        wiki, lists, team, contents, join = [l['name'] for l in links]
        self.assertEqual(wiki, u'Wiki')
        self.assertEqual(lists, u'Mailing Lists')
        self.assertEqual(team, u'Team')
        self.assertEqual(contents, u'Contents')
        self.assertEqual(join, u'Join Project')
        del req.environ['X_OPENPLANS_PROJECT']

        # test switch to member context with
        # X-OpenPlans-Person header set
        self.clearMemoCache()
        req.environ['X_OPENPLANS_PERSON'] = 'm1'
        topnav = getMultiAdapter((self.portal, req), name='oc-topnav')
        html = topnav.contextmenu
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(2, len(lis))
        self.assertEqual(False, lis[0]['selected'])
        self.assertEqual(False, lis[1]['selected'])
        self.assertEqual(u'Wiki', links[0]['name'])
        self.assertEqual(u'Profile', links[1]['name'])
        del req.environ['X_OPENPLANS_PERSON']

        # test X-OpenPlans-Person overrides
        # X-OpenPlans-Project
        self.clearMemoCache()
        req.environ['X_OPENPLANS_PROJECT'] = 'p1'
        req.environ['X_OPENPLANS_PERSON'] = 'm1'
        topnav = getMultiAdapter((self.portal, req), name='oc-topnav')
        html = topnav.contextmenu
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(2, len(lis))
        self.assertEqual(False, lis[0]['selected'])
        self.assertEqual(False, lis[1]['selected'])
        self.assertEqual(u'Wiki', links[0]['name'])
        self.assertEqual(u'Profile', links[1]['name'])
        del req.environ['X_OPENPLANS_PERSON']
        del req.environ['X_OPENPLANS_PROJECT']

        # test normal behavior when headers
        # are set to invalid values
        self.clearMemoCache()
        req.environ['X_OPENPLANS_PROJECT'] = 'GlUrT'
        req.environ['X_OPENPLANS_PERSON'] = 'PhL00m'
        topnav = getMultiAdapter((self.portal, req), name='oc-topnav')
        html = topnav.contextmenu
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(3, len(lis))
        for li in lis:
            self.assertEqual(False, li['selected'])
        people, projects, start = [l['name'] for l in links]
        self.assertEqual(people, u'People')
        self.assertEqual(projects, u'Projects')
        self.assertEqual(start, u'Start A Project')
        del req.environ['X_OPENPLANS_PERSON']
        del req.environ['X_OPENPLANS_PROJECT']


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
