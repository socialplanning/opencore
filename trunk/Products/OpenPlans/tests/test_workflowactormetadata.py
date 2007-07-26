"""
Working pieces now live in opencore.nui.indexing
"""
import os, sys
import unittest

from Products.CMFCore.utils import getToolByName

from opencore.testing.layer import OpencoreContent
from openplanstestcase import OpenPlansTestCase, makeContent

class TestWorkflowActorMetadata(OpenPlansTestCase):

    layer = OpencoreContent

    def afterSetUp(self):
        OpenPlansTestCase.afterSetUp(self)
        self.catalog = getToolByName(self.portal, 'portal_catalog')

    def test_worksForMembership(self):
        # create a membership object and make sure the
        # lastWorkflowActor metadata is stored correctly on the
        # catalog brain
        mem_id = 'm1'
        proj_id = 'p4' # <-- m1 is not a member of p4
        self.login(mem_id)

        tmtool = getToolByName(self.portal, 'portal_teams')
        team = tmtool._getOb(proj_id)
        team.join()

        cat = self.catalog
        team_path = '/'.join(team.getPhysicalPath())
        brains = cat(portal_type='OpenMembership',
                     path=team_path,
                     id = mem_id)
        self.assertEqual(len(brains), 1)
        brain = brains[0]
        self.assertEqual(brain.lastWorkflowActor, mem_id)

    def test_doesntWorkForOthers(self):
        # make sure there's no lastWorkflowActor metadata value for a
        # regular page object
        mem_id = 'm1'
        proj_id = 'p3' # <-- m1 is a ProjectAdmin for p3
        self.login(mem_id)

        proj = self.portal.projects._getOb(proj_id)
        page = proj._getOb(proj.getDefaultPage())

        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.doActionFor(page, 'team')
        page.reindexObject()

        cat = self.catalog
        page_path = '/'.join(page.getPhysicalPath())
        brains = cat(portal_type='Document',
                     path=page_path,
                     )
        self.assertEqual(len(brains), 1)
        brain = brains[0]
        self.failUnless(brain.lastWorkflowActor is None)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestWorkflowActorMetadata))
    return suite

