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

    def test_contextmenu(self):
        #XXX this is commented out because we now have different menu
        # requirements based on whether we are using sputnik or vanilla
        # openplans
        # these are really functional tests anyway, and belong in the
        # functional testing flunc suites in the appropriate package
        # it's commented out and not removed to serve as a temporary resource
        # guiding the necessary flunc tests
        pass
#        req = self.request
#        topnav = getMultiAdapter((self.portal, req), name='oc-topnav')
#        html = topnav.contextmenu
#
#        # lis is the set of li tags (list items) contained in this menu
#        lis, links = parse_topnav_context_menu(html)
#        self.assertEqual(3, len(lis))
#        for li in lis:
#            self.assertEqual(False, li['selected'])
#        people, projects, start = [l['name'] for l in links]
#        self.assertEqual(people, u'People')
#        self.assertEqual(projects, project_noun().title() + u's')
#        self.assertEqual(start, u'Start A %s' % project_noun().title())
#
#        self.clearMemoCache()
#        proj = self.portal.projects.p1
#        topnav = getMultiAdapter((proj, req), name='oc-topnav')
#        html = topnav.contextmenu
#
#        # lis is the set of li tags (list items) contained in this menu
#        # In this case, it is the tages for the features (e.g. pages, blog,
#        # mailing lists, etc.)
#        lis, links = parse_topnav_context_menu(html)
#
#        # God, I wish that people understood that python needs comments, too.
#        # Maybe if someone had commented this in the first place, the following
#        # comment would make sense
#        # the "lis" is 4 elements long (used to be 6!) and we need to be sure
#        # that this is always true.  There are no longer 6 elements in lis.
#        # Why this is true, I don't know, but now we can be sure!
#        self.assert_(4 <= len(lis) and len(lis) <= 6)
#
#        # Only the join element should be selected
#        flag = False
#        for li in lis:
#            if li['selected'] != False:                
#                self.assertEqual(u'oc-topnav-join', li['selected'])
#                flag = True
#        # ensure join element is selected
#        self.assertEqual(True, flag)
#
#        navigation = [link['name'] for link in links]
#        self.assert_(u'Pages' in navigation)
#        # Optional
#        #self.assert_(u'Blog' in navigation)
#        #self.assert_(u'Mailing Lists' in navigation)
#        self.assert_(u'Team' in navigation)
#        self.assert_(u'Contents' in navigation)
#        self.assert_(u'Join %s' % project_noun().title() in navigation)
#        self.assert_(u'Summary' in navigation)
#
#        self.clearMemoCache()
#        memhome = self.memhome
#        topnav = getMultiAdapter((memhome, req), name='oc-topnav')
#        html = topnav.contextmenu
#
#        # lis is the set of li tags (list items) contained in this menu
#        lis, links = parse_topnav_context_menu(html)
#        self.assertEqual(2, len(lis))
#        self.assertEqual(False, lis[0]['selected'])
#        self.assertEqual(False, lis[1]['selected'])
#        self.assertEqual(u'Profile', links[0]['name'])
#        self.assertEqual(u'Pages', links[1]['name'])
#
#        # test switch to project context with
#        # X-OpenPlans-Project header set
#        self.clearMemoCache()
#        req.environ['X_OPENPLANS_PROJECT'] = 'p1'
#        topnav = getMultiAdapter((self.portal, req), name='oc-topnav')
#        html = topnav.contextmenu
#        lis, links = parse_topnav_context_menu(html)
#
#        self.assert_(4 <= len(lis) and len(lis) <= 6)
#
#        # Only the join element should be selected
#        flag = False
#        for li in lis:
#            if li['selected'] != False:                
#                self.assertEqual(u'oc-topnav-join', li['selected'])
#                flag = True
#        # ensure join element is selected
#        self.assertEqual(True, flag)
#
#        navigation = [link['name'] for link in links]
#        self.assert_(u'Pages' in navigation)
#        # Optional
#        #self.assert_(u'Blog' in navigation)
#        #self.assert_(u'Mailing Lists' in navigation)
#        self.assert_(u'Team' in navigation)
#        self.assert_(u'Contents' in navigation)
#        self.assert_(u'Join %s' % project_noun().title() in navigation)
#        self.assert_(u'Summary' in navigation)
#        del req.environ['X_OPENPLANS_PROJECT']
#
#        # test switch to member context with
#        # X-OpenPlans-Person header set
#        self.clearMemoCache()
#        req.environ['X_OPENPLANS_PERSON'] = 'm1'
#        topnav = getMultiAdapter((self.portal, req), name='oc-topnav')
#        html = topnav.contextmenu
#        lis, links = parse_topnav_context_menu(html)
#        self.assertEqual(2, len(lis))
#        self.assertEqual(False, lis[0]['selected'])
#        self.assertEqual(False, lis[1]['selected'])
#        self.assertEqual(u'Profile', links[0]['name'])
#        self.assertEqual(u'Pages', links[1]['name'])
#        del req.environ['X_OPENPLANS_PERSON']
#
#        # test X-OpenPlans-Person overrides
#        # X-OpenPlans-Project
#        self.clearMemoCache()
#        req.environ['X_OPENPLANS_PROJECT'] = 'p1'
#        req.environ['X_OPENPLANS_PERSON'] = 'm1'
#        topnav = getMultiAdapter((self.portal, req), name='oc-topnav')
#        html = topnav.contextmenu
#        lis, links = parse_topnav_context_menu(html)
#        self.assertEqual(2, len(lis))
#        self.assertEqual(False, lis[0]['selected'])
#        self.assertEqual(False, lis[1]['selected'])
#        self.assertEqual(u'Profile', links[0]['name'])
#        self.assertEqual(u'Pages', links[1]['name'])
#        del req.environ['X_OPENPLANS_PERSON']
#        del req.environ['X_OPENPLANS_PROJECT']
#
#        # test normal behavior when headers
#        # are set to invalid values
#        self.clearMemoCache()
#        req.environ['X_OPENPLANS_PROJECT'] = 'GlUrT'
#        req.environ['X_OPENPLANS_PERSON'] = 'PhL00m'
#        topnav = getMultiAdapter((self.portal, req), name='oc-topnav')
#        html = topnav.contextmenu
#        lis, links = parse_topnav_context_menu(html)
#        self.assertEqual(3, len(lis))
#        for li in lis:
#            self.assertEqual(False, li['selected'])
#        people, projects, start = [l['name'] for l in links]
#        self.assertEqual(people, u'People')
#        self.assertEqual(projects, project_noun().title() + u's')
#        self.assertEqual(start, u'Start A %s' % project_noun().title())
#        del req.environ['X_OPENPLANS_PERSON']
#        del req.environ['X_OPENPLANS_PROJECT']


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
