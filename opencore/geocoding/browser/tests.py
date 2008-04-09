from opencore.geocoding.testing import readme_setup, readme_teardown
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import OpencoreContent as test_layer
from zope.testing import doctest
import unittest

optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")


def test_suite():
    from Products.CMFCore.utils import getToolByName
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import setup
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Testing.ZopeTestCase import installProduct
    from opencore.geocoding.view import get_geo_writer
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

    def get_response_output(view):
        """quick hack to be able to test output of views that call
        response.write or otherwise don't just return string data.

        Note that you get HTTP headers as well as the body - but ONLY
        on the first call in a doctest - I think because the request &
        response objects are re-used? This sucks, but I don't know how
        to hack around it right now, except to expect this in tests...
        """
        from cStringIO import StringIO
        response = view.request.RESPONSE
        response.stdout = StringIO()
        view()
        return response.stdout.getvalue()

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
