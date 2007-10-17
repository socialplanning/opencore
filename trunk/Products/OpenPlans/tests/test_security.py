import os, sys, time
import unittest
import traceback
from StringIO import StringIO
from Testing import ZopeTestCase
from Products.CMFCore.utils import getToolByName
from Products.OpenPlans.Extensions.create_test_content import create_test_content
from openplanstestcase import OpenPlansTestCase, makeContent

members_map = {'m1':{'fullname':'Member One',
                     'password':'testy',
                     'email':'notreal@xyxyxyxy.com',
                     'projects': {'p1':tuple(),
                                  'p2':tuple(),
                                  'p3':('ProjectAdmin',),
                                  },
                     },
               }

class TestOpenSecurity(OpenPlansTestCase):

    def test_permissions(self):
        # this should really be spread across a bunch of different
        # tests (so there would be a satisfying output of a bunch of
        # little dots when you run it), but the initial setup takes so
        # long that it's not worth doing again and again
        # XXX have you consider creating a fixture specifically for this test?
        self.loginAsPortalOwner()
        create_test_content(self.portal, m_map=members_map)
        
        uf = getToolByName(self.portal, 'acl_users')
        projects = self.portal.projects

        m1 = uf.getUser('m1')
        m2 = uf.getUser('m2')
        m3 = uf.getUser('m3')
        
        p1 = projects.p1
        p2 = projects.p2
        p3 = projects.p3
        p4 = projects.p4
        
        perm = 'ATContentTypes: Add Document'
        self.failUnless(m1.has_permission(perm, p1))
        self.failUnless(m1.has_permission(perm, p3))
        self.failIf(m1.has_permission(perm, p4))

        perm = 'Modify portal content'
        self.failIf(m1.has_permission(perm, p1))
        self.failUnless(m1.has_permission(perm, p3))
        self.failIf(m1.has_permission(perm, p4))

        perm = 'TeamSpace: Manage team memberships'
        self.failIf(m1.has_permission(perm, p1))
        self.failUnless(m1.has_permission(perm, p3))
        self.failIf(m1.has_permission(perm, p4))

        perm = 'Reply to item'
        self.failUnless(m1.has_permission(perm, p1))
        self.failUnless(m1.has_permission(perm, p3))
        self.failIf(m1.has_permission(perm, p4))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestOpenSecurity))
    return suite

