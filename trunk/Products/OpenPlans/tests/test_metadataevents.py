import os, sys

from Products.PloneTestCase import PloneTestCase
from zope.testing import doctest
optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

from Products.ZCatalog import CatalogBrains
CatalogBrains.GETOBJECT_RAISES=False
#ctc.setupCMFSite()
CatalogBrains.GETOBJECT_RAISES=True

from openplanstestcase import SiteSetupLayer

def test_suite():
    import unittest
    
    from Testing.ZopeTestCase import ZopeDocFileSuite

    suite = ZopeDocFileSuite('metadata.txt',
                             package='Products.OpenPlans',
                             test_class=PloneTestCase.PloneTestCase,
                             optionflags=optionflags)
    suite.layer = SiteSetupLayer
    return suite

