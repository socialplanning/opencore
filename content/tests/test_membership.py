import os, sys
import unittest

from Products.CMFCore.utils import getToolByName
from Products.TeamSpace.exceptions import MemberRoleNotAllowed

from opencore.testing.layer import OpencoreContent

from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase, \
     makeContent

class TestOpenMembership(OpenPlansTestCase):

    layer = OpencoreContent

    def afterSetUp(self):
        self.tmtool = getToolByName(self.portal, 'portal_teams')
        OpenPlansTestCase.afterSetUp(self)

    def test_editTeamRoles(self):
        tmtool = self.tmtool
        tm = tmtool.p1
        mship = tm.getMemberships()[0]
        roles = []
        for role in ('', 'ProjectMember', 'ProjectAdmin'):
            if role:
                roles.append(role)
            mship.editTeamRoles(roles)
            self.assertEqual(roles, mship.getTeamRoles())
        roles.append('Owner')
        self.assertRaises(MemberRoleNotAllowed, mship.editTeamRoles, roles)

    def test_canApproveOrReject(self):
        self.login('m1')
        tmtool = self.tmtool
        tm = tmtool.getTeamById('p4') # <- m1 is not a member
        
        # self can't approve, admin can
        tm.join()
        mship = tm._getOb('m1')
        self.failIf(mship is None)
        self.failIf(mship.canApprove())
        self.failIf(mship.canReject('owner'))

        self.login('m2') # <- project admin
        self.failUnless(mship.canApprove())
        self.failUnless(mship.canReject('admin'))
        tm.manage_delObjects(['m1'])

        # admin can't approve, self can
        tm.addMember('m1')
        mship = tm._getOb('m1')
        self.failIf(mship.canApprove())
        self.failIf(mship.canReject('admin'))

        self.login('m1')
        self.failUnless(mship.canApprove())
        self.failUnless(mship.canReject('owner'))

    def test_mshipOwnership(self):
        self.login('m1')
        tm = self.tmtool.getTeamById('p3') # <- m1 is admin, m4 isn't member
        tm.addMember('m4')
        mship = tm.getMembershipByMemberId('m4')
        owner_id = mship.owner_info()['id']
        self.failUnless(owner_id == 'm4')
        self.failUnless('Owner' in mship.get_local_roles_for_userid('m4'))
        self.failIf('Owner' in mship.get_local_roles_for_userid('m1'))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestOpenMembership))
    return suite
