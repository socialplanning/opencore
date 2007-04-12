import os, sys
import unittest

from Products.CMFCore.utils import getToolByName

from Products.OpenPlans.interfaces import IWriteWorkflowPolicySupport
from Products.OpenPlans.interfaces import IReadWorkflowPolicySupport
from openplanstestcase import OpenPlansTestCase, makeContent

class TestWorkflowPolicy(OpenPlansTestCase):

    def afterSetUp(self):
        OpenPlansTestCase.afterSetUp(self)
        mstool = getToolByName(self.portal, 'portal_membership')
        self.loginAsPortalOwner()
        mstool.getAuthenticatedMember() # wrap user
        self.proj = makeContent(self.folder, 'project1', 'OpenProject')

    def test_policyWriteRead(self):
        policy = 'open_policy'
        policy_writer = IWriteWorkflowPolicySupport(self.proj)
        policy_writer.setPolicy(policy)

        policy_reader = IReadWorkflowPolicySupport(self.proj)
        returned_policy = policy_reader.getCurrentPolicyId()
        self.failUnless(policy == returned_policy)

    def test_projectStateMatches(self):
        wftool = getToolByName(self.portal, 'portal_workflow')

        policy_writer = IWriteWorkflowPolicySupport(self.proj)
        policy_writer.setPolicy('closed_policy')
        proj_state = wftool.getInfoFor(self.proj, 'review_state')
        self.failUnless(proj_state == 'closed')

        policy_writer.setPolicy('open_policy')
        proj_state = wftool.getInfoFor(self.proj, 'review_state')
        self.failUnless(proj_state == 'open')

    def test_projectEditTriggersWFPolicyEdit(self):
        req = self.proj.REQUEST
        policy = 'closed_policy'
        req.set('workflow_policy', policy)
        self.proj.edit(title='Some New Title')

        policy_reader = IReadWorkflowPolicySupport(self.proj)
        returned_policy = policy_reader.getCurrentPolicyId()
        self.failUnless(policy == returned_policy)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestWorkflowPolicy))
    return suite

