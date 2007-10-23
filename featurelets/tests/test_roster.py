import os, sys
import unittest

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from zope.interface import directlyProvides
from zope.app.annotation.interfaces import IAttributeAnnotatable

from Testing.ZopeTestCase import ZopeTestCase

from topp.featurelets.interfaces import IFeatureletSupporter
from topp.featurelets.interfaces import IMenuSupporter
from opencore.featurelets.roster import RosterFeaturelet
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Products.OpenPlans.tests.openplanstestcase import makeContent


class TestRosterFeaturelet(OpenPlansTestCase):

    def afterSetUp(self):
        OpenPlansTestCase.afterSetUp(self)
        self.loginAsPortalOwner()
        self.project = makeContent(self.portal, 'project', 'OpenProject')

    def test_addFeaturelet(self):
        featurelet = RosterFeaturelet()
        self.assertEqual(self.project.objectIds(), [])
        team = makeContent(self.portal.portal_teams, 'Team', 'OpenTeam')
        self.project.setSpaceTeams([team])
        fletsupporter = IFeatureletSupporter(self.project)
        fletsupporter.installFeaturelet(featurelet)
        
        roster_id = featurelet._info['content'][0]['id']
        self.failUnless(roster_id in self.project.objectIds())
        roster = self.project._getOb(roster_id)
        self.failUnless(roster.getTeams() == [team])
        menusupporter = IMenuSupporter(self.project)
        menu_items = menusupporter.getMenuItems(featurelet._menu_id)
        item_title = featurelet._info['menu_items'][0]['title']
        self.failUnless(menu_items.has_key(item_title))

    def test_removeFeaturelet(self):
        featurelet = RosterFeaturelet()
        fletsupporter = IFeatureletSupporter(self.project)
        fletsupporter.installFeaturelet(featurelet)
        fletsupporter.removeFeaturelet(featurelet)

        roster_id = featurelet._info['content'][0]['id']
        self.failIf(roster_id in self.project.objectIds())
        menusupporter = IMenuSupporter(self.project)
        menu_items = menusupporter.getMenuItems(featurelet._menu_id)
        item_title = featurelet._info['menu_items'][0]['title']
        self.failIf(menu_items.has_key(item_title))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestRosterFeaturelet))
    return suite

if __name__ == '__main__':
    framework()
