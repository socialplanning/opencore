import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Testing.ZopeTestCase import FunctionalDocFileSuite
from opencore.testing.layer import OpencoreContent
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from zope.interface import alsoProvides
from opencore.listen.interfaces import IListenContainer
from opencore.testing.layer import MockHTTPWithContent
from zope.app.component.hooks import setSite
from Products.Five.site.localsite import enableLocalSiteHook
from zope.app.component.hooks import setSite, setHooks

#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import setup
    from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
    from Products.CMFCore.utils import getToolByName
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from pprint import pprint
    from zope.interface import alsoProvides
    from zope.component import getUtility
    from opencore.interfaces.workflow import IReadWorkflowPolicySupport
    from opencore.testing import utils
    from opencore.nui.indexing import authenticated_memberid

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
        
    def readme_setup(tc):
        tc._refreshSkinData()

    def metadata_setup(tc):
        tc.project = tc.portal.projects.p1
        tc.page = getattr(tc.project, 'project-home')

    def manage_team_setup(tc):
        from zope.app.component.site import setSite
        setSite(tc.portal)

    globs = locals()
    readme = FunctionalDocFileSuite("README.txt", 
                                    optionflags=optionflags,
                                    package='opencore.nui.project',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=readme_setup
                                    )
    
    metadata = FunctionalDocFileSuite("metadata.txt", 
                                    optionflags=optionflags,
                                    package='opencore.nui.project',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=metadata_setup
                                    )
    
    contents = FunctionalDocFileSuite("contents.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui.project',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    setUp=contents_content, 
                                    )

    manage_team = FunctionalDocFileSuite("manage-team.txt",
                                         optionflags=optionflags,
                                         package='opencore.nui.project',
                                         test_class=OpenPlansTestCase,
                                         globs = globs, 
                                         setUp=manage_team_setup
                                         )

    request_membership = FunctionalDocFileSuite("request-membership.txt",
                                                optionflags=optionflags,
                                                package='opencore.nui.project',
                                                test_class=OpenPlansTestCase,
                                                globs = globs, 
                                                setUp=manage_team_setup,
                                                )

    homepage = FunctionalDocFileSuite("homepage.txt",
                                                optionflags=optionflags,
                                                package='opencore.nui.project',
                                                test_class=OpenPlansTestCase,
                                                globs = globs, 
                                                setUp=manage_team_setup,
                                                )

#    preferences = FunctionalDocFileSuite("preferences.txt",
#                                         optionflags=optionflags,
#                                         package='opencore.nui.project',
#                                         test_class=OpenPlansTestCase,
#                                         globs = globs, 
#                                         setUp=manage_team_setup,
#                                         )    
#
#    suites = (contents, metadata, manage_team, request_membership, preferences)
    suites = (contents, metadata, manage_team, request_membership, homepage)
    for suite in suites:
        suite.layer = OpencoreContent
    readme.layer = MockHTTPWithContent
    unit = doctest.DocTestSuite('opencore.nui.project.view',
                                optionflags=optionflags)
    return unittest.TestSuite(suites + (readme, unit))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
