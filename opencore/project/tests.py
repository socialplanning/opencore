from Products.Five.site.localsite import enableLocalSiteHook
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Testing import ZopeTestCase
from Testing.ZopeTestCase import FunctionalDocFileSuite
from Testing.ZopeTestCase import PortalTestCase 
from opencore.project.test_workflowpolicy import test_suite as wftest
from opencore.testing.layer import OpencoreContent
from zope.app.component.hooks import setSite, setHooks
from zope.testing import doctest
import os
import sys
import unittest

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import setup
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from opencore import redirect
    from pprint import pprint
    from opencore.interfaces.event import AfterProjectAddedEvent, AfterSubProjectAddedEvent
    from opencore.testing import create_test_content
    from zope.interface import alsoProvides

    ZopeTestCase.installProduct('PleiadesGeocoder')
    setup.setupPloneSite(products=['PleiadesGeocoder'])

    def readme_setup(tc):
        tc._refreshSkinData()
        enableLocalSiteHook(tc.portal)
        setSite(tc.portal)
        setHooks()

    globs = locals()
    readme = FunctionalDocFileSuite("README.txt",
                                    optionflags=optionflags,
                                    package='opencore.project',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    setUp=readme_setup
                                    )

    readme.layer = OpencoreContent
    
    return unittest.TestSuite((readme, wftest()))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
