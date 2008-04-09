import os, sys, unittest
from zope.testing import doctest
from zope.app.component.hooks import setSite, setHooks
#from Products.Five.site.localsite import enableLocalSiteHook
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
    from opencore.browser.formhandler import test_suite as octotest
    from opencore.testing.utils import monkey_proj_noun, unmonkey_proj_noun
    from zope.component import getUtility
    from Products.listen.interfaces import IListLookup
    
    setup.setupPloneSite()

    def set_site(tc):
        #enableLocalSiteHook(tc.portal)
        setSite(tc.portal)
        setHooks()

    def listen_discussion_setup(tc):
        tc._refreshSkinData()
        tc.request = tc.app.REQUEST
        tc.response = tc.request.RESPONSE
        tc.homepage = getattr(tc.portal, 'site-home')
        tc.projects = tc.portal.projects
        set_site(tc)

    def listen_featurelet_setup(tc):
        set_site(tc)

    def teardown(tc):
        unmonkey_proj_noun()

    globs = locals()
    listen_discussion = FunctionalDocFileSuite("listen_discussion.txt",
                                    optionflags=optionflags,
                                    package='opencore.listen',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    setUp=listen_discussion_setup,
                                    tearDown=teardown,
                                    )

    listen_featurelet = FunctionalDocFileSuite("listen_featurelet.txt",
                                    optionflags=optionflags,
                                    package='opencore.listen',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    setUp=listen_featurelet_setup,
                                    )

    listen_discussion.layer = listen_featurelet.layer = test_layer

    return unittest.TestSuite((listen_discussion, listen_featurelet))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
