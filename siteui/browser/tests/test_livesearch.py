import os, sys

from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Products.ATContentTypes.tests.atcttestcase import ATCTFunctionalSiteTestCase 
from zope.testing import doctest
optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

class LiveSearchTestCase(ATCTFunctionalSiteTestCase):
    def tearDown(self):
        PortalTestCase.tearDown(self)

def test_suite():
    import unittest
    from Testing.ZopeTestCase import ZopeDocFileSuite, FunctionalDocFileSuite
    from Products.OpenPlans.tests.openplanstestcase import SiteSetupLayer
    suite = FunctionalDocFileSuite('livesearch.txt',
                                   package='Products.OpenPlans.browser.tests',
                                   test_class=LiveSearchTestCase,
                                   optionflags=optionflags)
    suite.layer = SiteSetupLayer
    return suite

