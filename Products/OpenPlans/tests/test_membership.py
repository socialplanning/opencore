import os, sys
import unittest

from Products.CMFCore.utils import getToolByName
from Products.TeamSpace.exceptions import MemberRoleNotAllowed

from opencore.testing.layer import OpencoreContent

from openplanstestcase import OpenPlansTestCase, makeContent

class TestOpenMembership(OpenPlansTestCase):

    layer = OpencoreContent

    def test_editTeamRoles(self):
        tmtool = self.portal.portal_teams
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

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestOpenMembership))
    return suite
