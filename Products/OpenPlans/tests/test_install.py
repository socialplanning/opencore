"""
tests the integrity of an installation as
installed by the customization policy
"""
import os, sys, time
import unittest
from sets import Set
import traceback
from StringIO import StringIO
from Testing import ZopeTestCase

from Products.CMFCore.utils import getToolByName
from Products.CMFCore import permissions
from Products.OpenPlans.workflows import PLACEFUL_POLICIES
from Products.OpenPlans.config import DEFAULT_ROLES
from openplanstestcase import OpenPlansTestCase, makeContent, \
     ArcheSiteTestCase
import Products.CMFCore
from Products.OpenPlans.interfaces import IWriteWorkflowPolicySupport, IReadWorkflowPolicySupport

from opencore.nui.indexing import PROJECT_POLICY as ppidx
from Products.OpenPlans.content.project import OpenProject 

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
        project_wf_config = pwf_tool.getWorkflowPolicyConfig(self.portal.projects)
        self.failUnless(project_wf_config)
        self.failUnless(project_wf_config.getPolicyBelowId())
            
    def test_install(self):
        # workflows are installed
        ttool = getToolByName(self.portal, 'portal_types')

        # roles are installed
        for role in DEFAULT_ROLES:
            self.failIf(role not in self.portal.validRoles())
        # top level content is correct
        self.failUnless('projects' \
                        in self.portal.contentIds(spec="ATBTreeFolder"))

        if hasattr(ttool, 'HelpCenter'):
            self.failUnless('support' \
                            in self.portal.contentIds(spec="HelpCenter"))

    def test_kupusetup(self):
        from Products.OpenPlans.Extensions.utils import kupu_libraries, kupu_resource_map
        from sets import Set
        kt = getToolByName(self.portal, 'kupu_library_tool')
        self.assertEqual(Set([kl['id'] for kl in kupu_libraries]),
                         Set([kl['id'] for kl in kt.zmi_get_libraries()]))

        krm = dict(kt.zmi_get_type_mapping())
        typetool = getToolByName(self.portal, 'portal_types')
        def typefilter(types):
            all_meta_types = dict([ (t.id, 1) for t in typetool.listTypeInfo()])
            return [ t for t in types if t in all_meta_types ]
        
        for key in krm.keys():
            self.assertEqual(Set(krm[key]), \
                             Set(typefilter(kupu_resource_map[key])))

        self.assertEqual(krm.keys(), kupu_resource_map.keys())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestOpenPlansInstall))
    return suite
