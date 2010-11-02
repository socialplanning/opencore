"""
tests the integrity of an installation as
installed by the customization policy
"""
import socket
import unittest

from Products.CMFCore.utils import getToolByName
from Products.CMFCore import permissions
from Products.OpenPlans.workflows import PLACEFUL_POLICIES
from opencore.configuration import DEFAULT_ROLES
from openplanstestcase import OpenPlansTestCase
from opencore.interfaces.workflow import IWriteWorkflowPolicySupport
from opencore.utils import get_workflow_policy_config
from opencore.utils import get_config
from opencore.nui.indexing import PROJECT_POLICY as ppidx
from Products.OpenPlans.content.project import OpenProject 

psheet_id = 'opencore_properties'

class TestOpenPlansInstall(OpenPlansTestCase):
    def afterSetUp(self):
        pass

    def test_edittab(self):
        pt=getToolByName(self.portal, 'portal_types')
        action=pt.Document._actions[1]
        self.assertEqual(action.permissions, (permissions.View,))

    def test_project_policy_index(self):
        catalog = getToolByName(self.portal, 'portal_catalog')
        self.assertEqual(ppidx in catalog.indexes(), True)
        self.portal.projects.invokeFactory(OpenProject.portal_type, id='testp')
        project = getattr(self.portal.projects, 'testp')
        IWriteWorkflowPolicySupport(project).setPolicy('closed_policy')
        project.reindexObject()
        brains = catalog(**{ppidx:'closed_policy'})
        self.assertEqual(len(brains), 1)
        self.assertEqual(brains[0].getObject(), project)

    def test_placefulworkflow(self):
        pwf_tool = getToolByName(self.portal, 'portal_placeful_workflow')
        for wf_id in PLACEFUL_POLICIES.keys():
            self.failIf(wf_id not in pwf_tool.objectIds())
        project_wf_config = get_workflow_policy_config(self.portal.projects)
        self.failUnless(project_wf_config)
        self.failUnless(project_wf_config.getPolicyBelowId())
            
    def test_propertysheetinstall(self):
        ptool = getToolByName(self.portal, 'portal_properties')
        self.failUnless(psheet_id in ptool.objectIds())
        psheet = ptool._getOb(psheet_id)
        self.failUnless(psheet.hasProperty('remote_auth_sites'))
        self.failUnless(psheet.hasProperty('mailing_list_fqdn'))

    def test_portalproperties(self):
        # portlets should be empty
        self.failIf(self.portal.getProperty('left_slots'))
        self.failIf(self.portal.getProperty('right_slots'))
        self.failIf(self.portal.getProperty('validate_email'))
        self.assertEqual(self.portal.getProperty('title'),
                         'OpenCore Site')
        try:
            addy = get_config('email_from_address')
            if addy is None:
                addy = 'greetings@%s' % socket.getfqdn()
        except:
            addy = 'greetings@%s' % socket.getfqdn()
        self.assertEqual(self.portal.getProperty('email_from_address'),
                         addy)

    def test_install(self):
        # workflows are installed
        ttool = getToolByName(self.portal, 'portal_types')

        # roles are installed
        for role in DEFAULT_ROLES:
            self.failIf(role not in self.portal.validRoles())
        # top level content is correct
        self.failUnless('projects' in self.portal.objectIds())

    def test_openproject_method_aliases(self):
        tt = getToolByName(self.portal, 'portal_types')
        aliases = tt.OpenProject.getMethodAliases()
        default_alias = aliases['(Default)']
        view_alias = aliases['view']
        edit_alias = aliases['edit']
        index_alias = aliases['index.html']

        self.failIf(default_alias == '(dynamic view)')
        self.failUnless(default_alias == '@@view')

        self.failUnless(view_alias == '@@view')
        self.failUnless(edit_alias == '@@preferences')
        self.failUnless(index_alias == '@@view')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestOpenPlansInstall))
    return suite
