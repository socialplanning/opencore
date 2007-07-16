import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import FunctionalDocFileSuite
from opencore.testing.layer import OpencoreContent as test_layer
from zope.app.component.site import setSite

#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import setup
    from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
    from Products.CMFCore.utils import getToolByName
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from pprint import pprint
    from zope.interface import alsoProvides
    from zope.component import getUtility
    from opencore.interfaces import IMemberFolder
    from opencore.nui.member.interfaces import ITransientMessage
    from opencore.nui.project.interfaces import IEmailInvites

    img = os.path.join(os.path.dirname(__file__), 'test-portrait.jpg')
    portrait = open(img)

    setup.setupPloneSite()
    def readme_setup(tc):
        tc._refreshSkinData()

        # we also need to set the site for the local utility
        setSite(tc.portal)

    globs = locals()
    readme = FunctionalDocFileSuite("README.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui.member',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    setUp=readme_setup
                                    )

    readme.layer = test_layer

    transient = FunctionalDocFileSuite('transient-message.txt',
                                 optionflags=optionflags,
                                 package='opencore.nui.member',
                                 test_class=OpenPlansTestCase,
                                 globs=globs,
                                 setUp=readme_setup
                                 )

    return unittest.TestSuite((readme, transient))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
