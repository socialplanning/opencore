from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Testing import ZopeTestCase
from opencore.geocoding.testing import readme_setup, readme_teardown
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import OpencoreContent as test_layer
from opencore.testing.setup import hook_setup
from zope.testing import doctest
import unittest

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")


def test_suite():
    from Products.PloneTestCase import setup
    from opencore.project.browser.base import ProjectBaseView
    from opencore.member.browser.view import ProfileView
    from pprint import pprint
    from Products.PleiadesGeocoder.interfaces import IGeoItemSimple
    from opencore.geocoding.interfaces import IGeoFolder, \
         IReadGeo, IWriteGeo, IReadWriteGeo, \
         IGeoreferenceable, IGeoAnnotatableContent, IGeoserializable, \
         IGeoserializableMembersFolder
    from opencore.geocoding.view import get_geo_reader
    from opencore.geocoding.view import get_geo_writer
    ZopeTestCase.installProduct('PleiadesGeocoder')
    setup.setupPloneSite()

    globs = locals()

    config = dtf.ZopeDocFileSuite('configuration.txt',
                                  optionflags=optionflags,
                                  package='opencore.geocoding',
                                  test_class=OpenPlansTestCase,
                                  globs=globs,
                                  setUp=hook_setup,
                                  layer=test_layer
                                  )
    readme = dtf.ZopeDocFileSuite("README.txt",
                                  optionflags=optionflags,
                                  package='opencore.geocoding',
                                  test_class=OpenPlansTestCase,
                                  globs = globs,
                                  setUp=readme_setup,
                                  tearDown=readme_teardown,
                                  layer=test_layer
                                  )
    utilsunit = doctest.DocTestSuite('opencore.geocoding.utils',
                                     optionflags=optionflags)
    return unittest.TestSuite((utilsunit,
                               config,
                               readme,))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
