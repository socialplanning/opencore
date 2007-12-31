from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Testing import ZopeTestCase
from opencore.geocoding.view import getReadGeoViewWrapper
from opencore.geocoding.view import getWriteGeoViewWrapper
from opencore.member.browser.view import ProfileView
from opencore.project.browser.view import ProjectBaseView
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import OpencoreContent as test_layer
from opencore.testing.setup import hook_setup
from zope.testing import doctest
import unittest

optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")


def geo_view_setup(tc):
    hook_setup(tc)
    tc.project = tc.portal.projects.p1
    # Have to make sure everything is acquisition-wrapped for tests, or else
    # security wouldn't be enforced.
    pview = ProjectBaseView(tc.project, tc.project.REQUEST).__of__(tc.project)
    tc.proj_writer = getWriteGeoViewWrapper(pview)
    tc.proj_reader = getReadGeoViewWrapper(pview)
##     memberarea = tc.portal.members.m1
##     mview = ProfileView(memberarea, memberarea.REQUEST).__of__(memberarea)
##     tc.mem_writer = getWriteGeoViewWrapper(mview)
##     tc.mem_reader = getReadGeoViewWrapper(mview)

def test_suite():
    from Products.PloneTestCase import setup
    from opencore.project.browser.view import ProjectBaseView
    from opencore.member.browser.view import ProfileView
    from pprint import pprint
    from Products.PleiadesGeocoder.interfaces import IGeoItemSimple
    from opencore.geocoding.interfaces import IGeoFolder, \
         IReadGeo, IWriteGeo, IReadWriteGeo, \
         IGeoreferenceable, IGeoAnnotatableContent, IGeoserializable, \
         IGeoserializableMembersFolder
    from opencore.geocoding.view import getReadGeoViewWrapper
    from opencore.geocoding.view import getWriteGeoViewWrapper
    ZopeTestCase.installProduct('PleiadesGeocoder')
    setup.setupPloneSite()

    globs = locals()

    config = dtf.ZopeDocFileSuite('configuration.txt',
                                  optionflags=optionflags,
                                  package='opencore.geocoding.tests',
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
                                  setUp=hook_setup,
                                  layer=test_layer
                                  )
    utilsunit = doctest.DocTestSuite('opencore.geocoding.utils',
                                     optionflags=optionflags)
    security = dtf.ZopeDocTestSuite('opencore.geocoding.tests.security',
                                    optionflags=optionflags,
                                    test_class=OpenPlansTestCase,
                                    globs=globs,
                                    setUp=geo_view_setup,
                                    layer=test_layer
                                    )

    return unittest.TestSuite((utilsunit,
                               config,
                               security,
                               readme,))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
