import os, sys
import unittest

from Testing import ZopeTestCase

import zope.event
from zope.app.event import objectevent
from zope.component import provideUtility
from zope.component import getAdapter
from zope.component import getUtility

from topp.featurelets.registry import FeatureletRegistry
from topp.featurelets.interfaces import IFeatureletRegistry
from topp.featurelets.interfaces import IMenuSupporter
from topp.featurelets.interfaces import IFeaturelet
from topp.featurelets.interfaces import IFeatureletSupporter

from Products.CMFCore.utils import getToolByName

from zope.app.component.hooks import setSite, setHooks
#from Products.Five.site.localsite import enableLocalSiteHook

from openplanstestcase import OpenPlansTestCase
from openplanstestcase import makeContent


class TestFeaturelets(OpenPlansTestCase):
    
    def afterSetUp(self):
        OpenPlansTestCase.afterSetUp(self)
        self.folder.manage_permission('OpenPlans: Add OpenProject',
                                      roles=('Manager', 'Owner'))
        self.proj = makeContent(self.folder, 'project1', 'OpenProject')
        #enableLocalSiteHook(self.portal)
        setSite(self.portal)
        setHooks()

    def test_featureletSupporterView(self):
        registry = getUtility(IFeatureletRegistry)
        flets = registry.getFeaturelets(supporter=self.proj)

        view = self.proj.restrictedTraverse('@@featurelet_support')
        flets_info = view.getSupportableFeaturelets()

        self.assertEqual(set([f.id for f in flets]),
                         set([f['id'] for f in flets_info]))

    def test_featureletsNotRemoved(self):
        # there was a bug where edits on the container that were not
        # from the edit template would cause all of the featurelets to
        # be uninstalled; this demonstrates that the bug has been
        # fixed
        flet_id = 'listen'
        content_id = 'lists'
        supporter = IFeatureletSupporter(self.proj)
        flet = getAdapter(supporter, IFeaturelet, flet_id)
        supporter.installFeaturelet(flet)
        self.failUnless(content_id in self.proj.objectIds())
        # unset the "don't recurse" flag
        req = self.proj.REQUEST
        req.set('flet_recurse_flag', None)

        zope.event.notify(objectevent.ObjectModifiedEvent(self.proj))
        self.failUnless(flet_id in supporter.getInstalledFeatureletIds())

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFeaturelets))
    return suite

