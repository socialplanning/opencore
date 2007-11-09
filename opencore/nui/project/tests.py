import os, sys, unittest
from opencore.nui.account import utils
utils.turn_confirmation_on()
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase
from opencore.testing.layer import OpencoreContent
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from zope.interface import alsoProvides
from opencore.featurelets.interfaces import IListenContainer
from opencore.testing.layer import MockHTTPWithContent
from opencore.testing import setup as oc_setup
from Products.Five.site.localsite import enableLocalSiteHook
from zope.app.component.hooks import setSite, setHooks
from opencore.testing import dtfactory as dtf

#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import setup
    from Products.CMFCore.utils import getToolByName
    from Testing.ZopeTestCase import installProduct
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from pprint import pprint
    from zope.interface import alsoProvides
    from zope.component import getUtility
    from opencore.interfaces.workflow import IReadWorkflowPolicySupport
    from opencore.testing import utils
    from opencore.nui.indexing import authenticated_memberid

    # @@ bah... crappy irregular import scheme
    from opencore.tasktracker.featurelet import TaskTrackerFeaturelet
    from opencore.featurelets.listen import ListenFeaturelet

    # for delet-project
    from topp.featurelets.interfaces import IFeatureletSupporter
    from topp.clockqueue.interfaces import IClockQueue
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

    globs = locals()
    readme = dtf.FunctionalDocFileSuite("README.txt", 
                                    optionflags=optionflags,
                                    package='opencore.nui.project',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=oc_setup.fresh_skin,
                                    layer = MockHTTPWithContent                                       
                                    )

    delete = dtf.FunctionalDocFileSuite("delete-project.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui.project',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    setUp=oc_setup.extended_tt_setup,
                                    layer = MockHTTPWithContent                                       
                                    )
    
    metadata = dtf.FunctionalDocFileSuite("metadata.txt", 
                                    optionflags=optionflags,
                                    package='opencore.nui.project',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=metadata_setup,
                                    layer=OpencoreContent     
                                    )
    
    contents = dtf.FunctionalDocFileSuite("contents.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui.project',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    setUp=contents_content,
                                    layer=OpencoreContent                                              
                                    )

    manage_team = dtf.FunctionalDocFileSuite("manage-team.txt",
                                         optionflags=optionflags,
                                         package='opencore.nui.project',
                                         test_class=OpenPlansTestCase,
                                         globs = globs, 
                                         setUp=oc_setup.set_portal_as_site,
                                         layer=OpencoreContent                                                 
                                         )

    request_membership = dtf.FunctionalDocFileSuite("request-membership.txt",
                                                optionflags=optionflags,
                                                package='opencore.nui.project',
                                                test_class=OpenPlansTestCase,
                                                globs = globs, 
                                                setUp=oc_setup.set_portal_as_site,
                                                layer=OpencoreContent                                                        
                                                )

    homepage = dtf.FunctionalDocFileSuite("homepage.txt",
                                                optionflags=optionflags,
                                                package='opencore.nui.project',
                                                test_class=OpenPlansTestCase,
                                                globs = globs, 
                                                setUp=oc_setup.set_portal_as_site,
                                                layer=OpencoreContent     
                                                )

    team_request_membership = dtf.FunctionalDocFileSuite("team_membership.txt",
                                                         optionflags=optionflags,
                                                         package='opencore.nui.project',
                                                         test_class=OpenPlansTestCase,
                                                         globs = globs, 
                                                         setUp=oc_setup.set_portal_as_site,
                                                         layer=OpencoreContent                                                 
                                                         )

##     preferences = FunctionalDocFileSuite("preferences.txt",
##                                          optionflags=optionflags,
##                                          package='opencore.nui.project',
##                                          test_class=OpenPlansTestCase,
##                                          globs = globs, 
##                                          setUp=manage_team_setup,
##                                          )    

##     suites = (contents, metadata, manage_team, request_membership, preferences)
    suites = (contents, metadata, manage_team,
              request_membership, homepage,
              team_request_membership)
    unit = doctest.DocTestSuite('opencore.nui.project.view',
                                optionflags=optionflags)
    return unittest.TestSuite(suites + (readme, unit, delete))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
