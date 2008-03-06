from opencore.account import utils
utils.turn_confirmation_on()
from Products.Five.site.localsite import enableLocalSiteHook
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase
from opencore.browser.base import BaseView
from opencore.configuration import OC_REQ
from opencore.featurelets.interfaces import IListenContainer
from opencore.tasktracker.testing.setup import extended_tt_setup
from opencore.testing import dtfactory as dtf
from opencore.testing import setup as oc_setup
from opencore.testing.layer import MockHTTPWithContent
from opencore.testing.layer import OpencoreContent
from zope.app.component.hooks import setSite, setHooks
from zope.interface import alsoProvides
from zope.testing import doctest
import os
import pkg_resources as pkgr
import sys
import unittest


#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Products.CMFCore.utils import getToolByName
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import setup
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Products.listen.interfaces import IListLookup
    from Testing.ZopeTestCase import installProduct
    from opencore.interfaces.workflow import IReadWorkflowPolicySupport
    from opencore.listen.featurelet import ListenFeaturelet
    from opencore.nui.indexing import authenticated_memberid
    from opencore.tasktracker.featurelet import TaskTrackerFeaturelet

    # for delete-project
    from opencore.testing import utils
    from opencore.testing.utils import clear_status_messages
    from opencore.testing.utils import get_status_messages
    from pprint import pprint
    from topp.clockqueue.interfaces import IClockQueue
    from opencore.listen.featurelet import ListenFeaturelet

    # for delete-project
    from topp.featurelets.interfaces import IFeatureletSupporter
    
    from zope.component import getUtility
    from zope.interface import alsoProvides
    import pdb
        
    setup.setupPloneSite()

    def contents_content(tc):
        tc.loginAsPortalOwner()
        proj = tc.portal.projects.p2
        proj.invokeFactory('Document', 'new1', title='new title')
        proj.invokeFactory('Image', 'img1', title='new image')
        proj.restrictedTraverse('project-home').invokeFactory('FileAttachment', 'fa1', title='new file')
        proj.new1.invokeFactory('FileAttachment', 'fa2', title='new1 file')
        proj.invokeFactory('Folder', 'lists', title='Listen Stub')
        lists = proj.lists
        lists.setLayout('mailing_lists')
        alsoProvides(lists, IListenContainer)
        enableLocalSiteHook(tc.portal)
        setSite(tc.portal)
        setHooks()
        proj.lists.invokeFactory('Open Mailing List', 'list1', title=u'new list')
        
    def metadata_setup(tc):
        tc.project = tc.portal.projects.p1
        tc.page = getattr(tc.project, 'project-home')

    def readme_setup(tc):
        oc_setup.fresh_skin(tc)
        enableLocalSiteHook(tc.portal)
        setSite(tc.portal)
        setHooks()
        # Force geocoding off for these tests.
        # (ie. even if it's installed, act like it isn't.)
        BaseView._old_has_geocoder = BaseView.has_geocoder
        BaseView.has_geocoder = False

    def readme_teardown(tc):
        BaseView.has_geocoder = BaseView._old_has_geocoder
        

    def tasktracker_setup(tc):
        extended_tt_setup(tc)
        enableLocalSiteHook(tc.portal)
        setSite(tc.portal)
        setHooks()

    test_file = pkgr.resource_stream(OC_REQ, 'opencore/project/browser/test.png')
    globs = locals()
    readme = dtf.ZopeDocFileSuite("README.txt", 
                                    optionflags=optionflags,
                                    package='opencore.project.browser',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=readme_setup,
                                    tearDown=readme_teardown,
                                    layer = MockHTTPWithContent,
                                    )

    logo = dtf.FunctionalDocFileSuite("logo.txt",
                                      optionflags=optionflags,
                                      package='opencore.project.browser',
                                      test_class=OpenPlansTestCase,
                                      globs=globs,
                                      setUp=readme_setup,
                                      tearDown=readme_teardown,
                                      layer=MockHTTPWithContent                                       
                                      )

    delete = dtf.ZopeDocFileSuite("delete-project.txt",
                                    optionflags=optionflags,
                                    package='opencore.project.browser',
                                    test_class=OpenPlansTestCase,
                                    globs=globs,
                                    setUp=tasktracker_setup,
                                    layer=MockHTTPWithContent                                       
                                    )
    
    metadata = dtf.ZopeDocFileSuite("metadata.txt", 
                                    optionflags=optionflags,
                                    package='opencore.project.browser',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=metadata_setup,
                                    layer=OpencoreContent     
                                    )
    
    contents = dtf.ZopeDocFileSuite("contents.txt",
                                    optionflags=optionflags,
                                    package='opencore.project.browser',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    setUp=contents_content,
                                    layer=OpencoreContent                                              
                                    )

    manage_team = dtf.ZopeDocFileSuite("manage-team.txt",
                                         optionflags=optionflags,
                                         package='opencore.project.browser',
                                         test_class=OpenPlansTestCase,
                                         globs = globs, 
                                         setUp=oc_setup.set_portal_as_site,
                                         layer=OpencoreContent                                                 
                                         )

    request_membership = dtf.ZopeDocFileSuite("request-membership.txt",
                                                optionflags=optionflags,
                                                package='opencore.project.browser',
                                                test_class=OpenPlansTestCase,
                                                globs = globs, 
                                                setUp=oc_setup.set_portal_as_site,
                                                layer=OpencoreContent                                                        
                                                )

    homepage = dtf.ZopeDocFileSuite("homepage.txt",
                                    optionflags=optionflags,
                                    package='opencore.project.browser',
                                    test_class=OpenPlansTestCase,
                                    globs = globs, 
                                    setUp=oc_setup.set_portal_as_site,
                                    layer=OpencoreContent     
                                    )

    team_request_membership = dtf.FunctionalDocFileSuite("team_membership.txt",
                                                         optionflags=optionflags,
                                                         package='opencore.project.browser',
                                                         test_class=OpenPlansTestCase,
                                                         globs = globs, 
                                                         setUp=oc_setup.set_portal_as_site,
                                                         layer=OpencoreContent                                                 
                                                         )
    

    utilsunit = doctest.DocTestSuite('opencore.project.browser.utils',  # XXX no tests in there?
                                     optionflags=optionflags)
    suites = (contents, metadata, manage_team,
              request_membership, homepage,
              team_request_membership, logo,
              readme, utilsunit, delete,
              )
    return unittest.TestSuite(suites)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
