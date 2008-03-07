from opencore.account import utils
utils.turn_confirmation_on()
from Products.Five.site.localsite import enableLocalSiteHook
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase
from opencore.configuration import OC_REQ
from opencore.featurelets.interfaces import IListenContainer
from opencore.testing import dtfactory as dtf
from opencore.testing import setup as oc_setup
from opencore.testing.layer import OpencoreContent
from zope.app.component.hooks import setSite, setHooks
from zope.interface import alsoProvides
from zope.testing import doctest
import os
import sys
import unittest
import pkg_resources as pkgr

#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Products.CMFCore.utils import getToolByName
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import setup
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Testing.ZopeTestCase import installProduct
    from opencore.interfaces.workflow import IReadWorkflowPolicySupport
    from opencore.listen.featurelet import ListenFeaturelet
    from opencore.nui.indexing import authenticated_memberid
    from opencore.tasktracker.featurelet import TaskTrackerFeaturelet
    from opencore.testing import utils
    from pprint import pprint
    from topp.clockqueue.interfaces import IClockQueue
    from topp.featurelets.interfaces import IFeatureletSupporter
    from zope.component import getUtility
    from zope.interface import alsoProvides
    import pdb
        
    setup.setupPloneSite()

    def readme_setup(tc):
        oc_setup.fresh_skin(tc)
        enableLocalSiteHook(tc.portal)
        setSite(tc.portal)
        setHooks()

    globs = locals()
    readme = dtf.ZopeDocFileSuite("README.txt", 
                                  optionflags=optionflags,
                                  package='opencore.feed.browser',
                                  test_class=FunctionalTestCase,
                                  globs = globs,
                                  setUp=readme_setup,
                                  layer = OpencoreContent                                       
                                  )

    return unittest.TestSuite((readme,))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
