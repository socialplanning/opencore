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
        mtool = getToolByName(self.portal, 'portal_membership')
        mtool.createMemberArea('m1')
        self.memhome = memhome = self.portal.people.m1
        alsoProvides(memhome, IMemberFolder)

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
        self.assertEqual(6, len(lis))
        for li in lis[:5]:
            self.assertEqual(False, li['selected'])
        self.assertEqual(u'oc-topnav-join', lis[5]['selected'])
        wiki, blog, lists, team, contents, join = [l['name'] for l in links]
        self.assertEqual(wiki, u'Wiki')
        self.assertEqual(blog, u'Blog')
        self.assertEqual(lists, u'Mailing Lists')
        self.assertEqual(team, u'Team')
        self.assertEqual(contents, u'Contents')
        self.assertEqual(join, u'Join Project')

        self.clearMemoCache()
        memhome = self.memhome
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
        self.assertEqual(6, len(lis))
        for li in lis[:5]:
            self.assertEqual(False, li['selected'])
        self.assertEqual(u'oc-topnav-join', lis[5]['selected'])
        wiki, blog, lists, team, contents, join = [l['name'] for l in links]
        self.assertEqual(wiki, u'Wiki')
        self.assertEqual(blog, u'Blog')
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
        req.ACTUAL_URL += '/plone/people/m1/profile'
        self.login('m1')
        topnav = getMultiAdapter((self.memhome, req), name='oc-topnav')
        html = topnav.contextmenu
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(3, len(lis))
        self.assertEqual(False, lis[0]['selected'])
        self.assertEqual('oc-topnav-selected', lis[1]['selected'])
        self.assertEqual(False, lis[2]['selected'])
        self.assertEqual(u'Wiki', links[0]['name'])
        self.assertEqual(u'Profile', links[1]['name'])
        self.assertEqual(u'Account', links[2]['name'])

        self.clearMemoCache()
        self.logout()
        topnav = getMultiAdapter((self.memhome, req), name='oc-topnav')
        html = topnav.contextmenu
        lis, links = parse_topnav_context_menu(html)
        self.assertEqual(2, len(lis))
        self.assertEqual(False, lis[0]['selected'])
        self.assertEqual(u'oc-topnav-selected', lis[1]['selected'])
        self.assertEqual(u'Wiki', links[0]['name'])
        self.assertEqual(u'Profile', links[1]['name'])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTopNav))
    return suite
