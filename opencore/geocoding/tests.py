from Products.Five.site.localsite import enableLocalSiteHook
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Testing import ZopeTestCase
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import OpencoreContent as test_layer
from zope.app.component.hooks import setSite, setHooks
from zope.testing import doctest
import unittest

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Products.PloneTestCase import setup
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from opencore import redirect
    from pprint import pprint

    installProduct('PleiadesGeocoder')
    setup.setupPloneSite()

    def hook_setup(tc):
        tc._refreshSkinData()
        enableLocalSiteHook(tc.portal)
        setSite(tc.portal)
        setHooks()

    globs = locals()
    readme = dtf.ZopeDocFileSuite("README.txt",
                                  optionflags=optionflags,
                                  package='opencore.geocoding',
                                  test_class=OpenPlansTestCase,
                                  globs = globs,
                                  setUp=hook_setup,
                                  layer=test_layer
                                  )

    return unittest.TestSuite((readme,))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
