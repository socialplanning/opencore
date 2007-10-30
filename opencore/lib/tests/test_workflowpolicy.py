import os, sys
import unittest

from Products.CMFCore.utils import getToolByName

from opencore.interfaces.workflow import IWriteWorkflowPolicySupport
from opencore.interfaces.workflow import IReadWorkflowPolicySupport

from opencore.nui.project.view import ProjectAddView

from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase, \
     makeContent

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
        req.form = {'workflow_policy': policy,
                    'title': 'Some New Title',
                    }
        self.proj.processForm(REQUEST=req)

        policy_reader = IReadWorkflowPolicySupport(self.proj)
        returned_policy = policy_reader.getCurrentPolicyId()
        self.failUnless(policy == returned_policy)

    def test_initialProjectStateIsRight(self):
        form = {'projid': 'closed',
                'title': 'Closed Project',
                'workflow_policy': 'closed_policy',
                'add': 'submit',
                }
        req = self.folder.REQUEST
        req.form = form
        addview = ProjectAddView(self.folder, req)
        addview.handle_request()
        proj = self.folder._getOb('closed')
        wftool = getToolByName(self.folder, 'portal_workflow')
        status = wftool.getInfoFor(proj, 'review_state')
        self.failUnless(status == 'closed')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestWorkflowPolicy))
    return suite

