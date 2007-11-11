import os, sys
import unittest

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Products.OpenPlans.tests.openplanstestcase import makeContent

from zope.app.annotation.interfaces import IAttributeAnnotatable
from zope.component import getMultiAdapter
from zope.component import ComponentLookupError
from zope.interface import directlyProvides
from zope.interface import Interface

from Testing.ZopeTestCase import ZopeTestCase

from zope.app.component.hooks import setSite, setHooks
from Products.Five.site.localsite import enableLocalSiteHook

from topp.featurelets.interfaces import IFeatureletSupporter
from topp.featurelets.interfaces import IMenuSupporter
from opencore.featurelets.listen import ListenFeaturelet
from opencore.featurelets.browser.listen import ListenConfigView

class TestListenFeaturelet(OpenPlansTestCase):

    def afterSetUp(self):
        OpenPlansTestCase.afterSetUp(self)
        self.loginAsPortalOwner()
        self.project = makeContent(self.portal, 'project', 'OpenProject')
        enableLocalSiteHook(self.portal)
        setSite(self.portal)
        setHooks()

    def test_addFeaturelet(self):
        featurelet = ListenFeaturelet()
        team = makeContent(self.portal.portal_teams, 'Team', 'OpenTeam')
        self.project.setSpaceTeams([team])
        self.assertEqual(self.project.objectIds(), [])
        request = self.project.REQUEST
        try:
            view = getMultiAdapter((self.project, request),
                                   Interface, ListenFeaturelet.config_view)
        except ComponentLookupError:
            pass
        else:
            self.fail("Config view shouldn't be available until the "
                      "featurelet is installed.")
        fletsupporter = IFeatureletSupporter(self.project)
        fletsupporter.installFeaturelet(featurelet)

        list_folder_id = featurelet._info['content'][0]['id']
        self.failUnless(list_folder_id in self.project.objectIds())
        menusupporter = IMenuSupporter(self.project)
        menu_items = menusupporter.getMenuItems(featurelet._menu_id)
        item_title = featurelet._info['menu_items'][0]['title']
        self.failUnless(menu_items.has_key(item_title))

        #try:
        #    view = getMultiAdapter((self.project, request),
        #                           Interface, ListenFeaturelet.config_view)
        #except ComponentLookupError:
        #    self.fail("Config view should be available after the "
        #              "featurelet is installed.")

    def test_removeFeaturelet(self):
        featurelet = ListenFeaturelet()
        fletsupporter = IFeatureletSupporter(self.project)
        fletsupporter.installFeaturelet(featurelet)
        fletsupporter.removeFeaturelet(featurelet)

        list_folder_id = featurelet._info['content'][0]['id']
        self.failIf(list_folder_id in self.project.objectIds())
        menusupporter = IMenuSupporter(self.project)
        menu_items = menusupporter.getMenuItems(featurelet._menu_id)
        item_title = featurelet._info['menu_items'][0]['title']
        self.failIf(menu_items.has_key(item_title))

        request = self.project.REQUEST
        try:
            view = getMultiAdapter((self.project, request),
                                   Interface, ListenFeaturelet.config_view)
        except ComponentLookupError:
            pass
        else:
            self.fail("Config view shouldn't be available after the "
                      "featurelet has been removed.")

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestListenFeaturelet))
    return suite

if __name__ == '__main__':
    framework()
