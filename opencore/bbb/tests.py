import unittest
from Products.OpenPlans.tests.test_featurelets import test_suite as featurelets
from Products.OpenPlans.tests.test_install import test_suite as install
from Products.OpenPlans.tests.test_views import test_suite as views
from Products.OpenPlans.tests.test_workflowactormetadata import test_suite as wf

suite_func = views, wf, featurelets, install, 

def test_suite():
    suite = unittest.TestSuite()
    for func in suite_func:
        suite.addTest(func())
    return suite
