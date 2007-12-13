import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from opencore.testing import dtfactory as dtf 
from opencore.testing.layer import OpenPlansLayer as test_layer
#from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase

#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import setup
    from Products.PloneTestCase.PloneTestCase import PloneTestCase
    from pprint import pprint
    from zope.interface import alsoProvides, Interface, implements 
    from zope.component import getUtility
    from zope.app.component.hooks import setSite
    from zope import component as zcomp
    from StringIO import StringIO
    from OFS.SimpleItem import SimpleItem


    class INumberOne(Interface):
        """pseudo iface #one"""

    class Utility(SimpleItem):
        implements(INumberOne)
    
    globs = locals()

    def setup(tc):
        setSite(tc.portal)

    local_utility_reg = dtf.ZopeDocFileSuite("local_utility_registration.txt",
                                             optionflags=optionflags,
                                             package='opencore.configuration',
                                             globs=globs,
                                             test_class=PloneTestCase,
                                             layer=test_layer,
                                             setUp=setup
                                             )
    return unittest.TestSuite((local_utility_reg,))
