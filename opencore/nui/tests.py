import unittest
from zope.testing import doctest
from opencore.testing.layer import OpencoreContent as test_layer
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from opencore.testing import dtfactory as dtf
from opencore.testing.setup import simple_setup

#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import setup
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from pprint import pprint
    from zope.interface import alsoProvides
    
    setup.setupPloneSite()

    globs = locals()
    setup = dtf.ZopeDocFileSuite("setup.txt",
                                 optionflags=optionflags,
                                 package='opencore.nui',
                                 test_class=OpenPlansTestCase,
                                 globs = globs,
                                 setUp=simple_setup,
                                 layer=test_layer
                                 )

    email_sender = dtf.ZopeDocFileSuite("email-sender.txt",
                                        optionflags=optionflags,
                                        package='opencore.nui',
                                        test_class=OpenPlansTestCase,
                                        globs = globs,
                                        setUp=simple_setup,
                                        layer=test_layer
                                        )

    return unittest.TestSuite((email_sender, setup))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
