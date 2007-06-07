import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Testing.ZopeTestCase import FunctionalDocFileSuite
from opencore.testing.layer import OpencoreContent

#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

class EthanLayer(OpencoreContent):
    @classmethod
    def tearDown(cls):
        raise NotImplementedError

def test_suite():
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import setup
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from pprint import pprint
    from zope.interface import alsoProvides
    from Products.OpenPlans.interfaces import IReadWorkflowPolicySupport
    from opencore.project.browser.projectinfo import get_featurelets
    from zope.app.annotation.interfaces import IAnnotations
    #setup.setupPloneSite()

    def contents_content(tc):
        tc.loginAsPortalOwner()
        proj = tc.portal.projects.p1
        proj.invokeFactory('Document', 'new1', title='new title')
        proj.invokeFactory('Image', 'img1', title='new file')
        proj.new1.invokeFactory('FileAttachment', 'fa1', title='new file')

        tc.image = proj.img1
        tc.page = proj.new1
        tc.att = tc.page.fa1

    def readme_setup(tc):
        tc._refreshSkinData()

    globs = locals()
    readme = FunctionalDocFileSuite("README.txt", 
                                    optionflags=optionflags,
                                    package='opencore.nui.project',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=readme_setup
                                    )
    contents = FunctionalDocFileSuite("contents.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui.project',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=contents_content, 
                                    )

    readme.layer = OpencoreContent
    contents.layer = OpencoreContent

    return unittest.TestSuite((readme, contents))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
