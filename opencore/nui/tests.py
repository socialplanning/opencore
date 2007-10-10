import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Testing.ZopeTestCase import FunctionalDocFileSuite
from opencore.testing.layer import OpencoreContent as test_layer
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase

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
    from pprint import pprint
    from opencore.nui.formhandler import test_suite as octotest
    
    setup.setupPloneSite()
    def readme_setup(tc):
        tc._refreshSkinData()
        tc.request = tc.app.REQUEST
        tc.response = tc.request.RESPONSE
        tc.homepage = getattr(tc.portal, 'site-home')
        tc.projects = tc.portal.projects

    globs = locals()
    readme = FunctionalDocFileSuite("README.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    setUp=readme_setup
                                    )

    readme.layer = test_layer
    
    setup = FunctionalDocFileSuite("setup.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    setUp=readme_setup
                                    )
    setup.layer = test_layer

    email_sender = FunctionalDocFileSuite("email-sender.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    setUp=readme_setup
                                    )

    email_sender.layer = test_layer

    placeful_workflow = FunctionalDocFileSuite("placeful_workflow_test.txt",
                                               optionflags=optionflags,
                                               package='opencore.nui',
                                               test_class=OpenPlansTestCase,
                                               globs = globs,
                                               setUp=readme_setup
                                               )

    placeful_workflow.layer = test_layer

    placeful_workflow = FunctionalDocFileSuite("member_info_test.txt",
                                               optionflags=optionflags,
                                               package='opencore.nui',
                                               test_class=OpenPlansTestCase,
                                               globs = globs,
                                               setUp=readme_setup
                                               )

    placeful_workflow.layer = test_layer

    return unittest.TestSuite((readme, octotest(), email_sender, placeful_workflow, setup))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
