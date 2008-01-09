from Products.Five.site.localsite import enableLocalSiteHook
from opencore.geocoding.testing import setup_mock_geocoder, restore_geocoder
from opencore.testing import dtfactory as dtf
from opencore.testing import setup as oc_setup
from opencore.testing.layer import OpencoreContent as test_layer
from zope.app.component.hooks import setSite, setHooks
from zope.testing import doctest
import unittest

optionflags = doctest.ELLIPSIS | doctest.REPORT_NDIFF

import warnings; warnings.filterwarnings("ignore")


def test_suite():
    from Products.CMFCore.utils import getToolByName
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import setup
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Testing.ZopeTestCase import installProduct
    from opencore.geocoding.view import getWriteGeoViewWrapper
    from opencore.testing import utils
    from pprint import pprint
    from zope.component import getUtility
    from zope.interface import alsoProvides
    from Products.PleiadesGeocoder.interfaces import IGeoItemSimple
    import pdb

    installProduct('PleiadesGeocoder')
    # Don't need to do setupPloneSite(products=['PleiadesGeocoder']) because
    # we'll use a mock instead.
    setup.setupPloneSite()
    project_name = 'p3'
    project_admin = 'm1'
    member = 'm2'

    def readme_setup(tc):
        oc_setup.fresh_skin(tc)
        enableLocalSiteHook(tc.portal)
        setSite(tc.portal)
        setHooks()
        setup_mock_geocoder()

    def readme_teardown(tc):
        restore_geocoder()

    globs = locals()
    readme = dtf.FunctionalDocFileSuite(
        "README.txt", 
        optionflags=optionflags,
        package='opencore.geocoding.browser',
        test_class=FunctionalTestCase,
        globs = globs,
        setUp=readme_setup,
        tearDown=readme_teardown,
        layer = test_layer
        )

    suites = (readme, )
    return unittest.TestSuite(suites)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
