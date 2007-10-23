import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Testing.ZopeTestCase import FunctionalDocFileSuite
from opencore.testing.layer import OpencoreContent

#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def replace_datetimeidx(idx, cat):
    """ replace the datetime index w/ a field index b/c we need
    better than 1 minute resolution for our testing """
    cat.delIndex(idx)
    cat.manage_addIndex(idx, 'FieldIndex',
                        extra={'indexed_attrs':idx})
    cat.manage_reindexIndex(ids=[idx])

def test_suite():
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import setup
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from pprint import pprint
    from zope.interface import alsoProvides

    setup.setupPloneSite()

    globs = locals()
    def setup(tc):
        catalog = tc.portal.portal_catalog
        for idx in 'created', 'modified':
            replace_datetimeidx(idx, catalog)
        
    search = FunctionalDocFileSuite("search.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui.main',
                                    test_class=FunctionalTestCase,
                                    setUp=setup,
                                    globs = globs,
                                    )
    search.layer = OpencoreContent

    return unittest.TestSuite((search,))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
