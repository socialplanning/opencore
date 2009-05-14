from opencore.account import utils
utils.turn_confirmation_on()
from Products.CMFCore.tests.base.testcase import LogInterceptor
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
from opencore.configuration import OC_REQ
from opencore.featurelets.interfaces import IListenContainer
from opencore.testing import dtfactory as dtf
from opencore.testing import setup as oc_setup
from opencore.testing.layer import OpencoreContent
from zope.app.component.hooks import setSite, setHooks
from zope.testing import doctest
import logging
import pkg_resources as pkgr
import unittest


#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")


class LoggingTestCase(FunctionalTestCase, object):
    # Based on LogInterceptor from CMFCore, but a bit easier to use, 
    # and reliably restores the state of the world on teardown.

    logged = None
    installed = ()
    level = 0

    def _start_log_capture(self,
                           min_capture_level=logging.INFO,
                           max_capture_level=logging.FATAL,
                           subsystem=''):
        logger = logging.getLogger(subsystem)
        # Need to patch the logger level to force it to handle the
        # messages we want to capture.
        self._old_logger_level, logger.level = logger.level, min_capture_level
        if subsystem in self.installed:
            # we're already handling this logger.
            return
        self.installed += (subsystem,)
        self.min_capture_level = min_capture_level
        self.max_capture_level = max_capture_level
        logger.addFilter(self)

    def filter(self, record):
        # Standard python logging filter API. False = reject this message.
        if self.logged is None:
            self.logged = []
        if record.levelno < self.min_capture_level or \
                record.levelno > self.max_capture_level:
            # pass it along but don't capture it.
            return True
        self.logged.append(record)
        return False  # reject it before any other handlers see it.

    def _stop_log_capture(self, subsystem=''):
        if subsystem not in self.installed:
            return
        logger = logging.getLogger(subsystem)
        logger.removeFilter(self)
        logger.level = self._old_logger_level
        self.installed = tuple([s for s in self.installed if s != subsystem])

    def tearDown(self):
        for subsystem in self.installed:
            self._stop_log_capture(subsystem)
        super(LoggingTestCase, self).tearDown()


def test_suite():
    from Products.CMFCore.utils import getToolByName
    from Products.PloneTestCase import setup
    from Products.listen.interfaces import IListLookup
    from Testing.ZopeTestCase import installProduct
    from opencore.interfaces.workflow import IReadWorkflowPolicySupport
    from opencore.listen.featurelet import ListenFeaturelet
    from opencore.nui.indexing import authenticated_memberid

    # for delete-project
    from opencore.testing import utils
    from opencore.testing.utils import clear_status_messages
    from opencore.testing.utils import get_status_messages
    from pprint import pprint
    from opencore.listen.featurelet import ListenFeaturelet

    # for delete-project
    from topp.featurelets.interfaces import IFeatureletSupporter
    
    from zope.component import getUtility
    from zope.interface import alsoProvides
        
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
        setSite(tc.portal)
        setHooks()
        proj.lists.invokeFactory('Open Mailing List', 'list1', title=u'new list')
        
    def metadata_setup(tc):
        tc.project = tc.portal.projects.p1
        tc.page = getattr(tc.project, 'project-home')

    def readme_setup(tc):
        oc_setup.fresh_skin(tc)
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
                                    layer = OpencoreContent,
                                  )
    export = dtf.ZopeDocFileSuite("export.txt",
                                  optionflags=optionflags,
                                  package='opencore.project.browser',
                                  test_class=LoggingTestCase,
                                  globs = globs,
                                  setUp=readme_setup,
                                  layer = OpencoreContent,
                                  )

    team_view = dtf.ZopeDocFileSuite("team-view.txt", 
                                    optionflags=optionflags,
                                    package='opencore.project.browser',
                                    test_class=FunctionalTestCase,
                                    globs = globs,
                                    setUp=readme_setup,
                                    layer = OpencoreContent,
                                    )

    logo = dtf.FunctionalDocFileSuite("logo.txt",
                                      optionflags=optionflags,
                                      package='opencore.project.browser',
                                      test_class=OpenPlansTestCase,
                                      globs=globs,
                                      setUp=readme_setup,
                                      layer=OpencoreContent                                       
                                      )

    delete = dtf.ZopeDocFileSuite("delete-project.txt",
                                  optionflags=optionflags,
                                  package='opencore.project.browser',
                                  test_class=OpenPlansTestCase,
                                  globs=globs,
                                  setUp=readme_setup,
                                  layer=OpencoreContent                                       
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

    contents = dtf.ZopeDocFileSuite("security_context.txt",
                                    optionflags=optionflags,
                                    package='opencore.project.browser',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    setUp=contents_content,
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
    
    suites = (contents,
              metadata,
              manage_team,
              request_membership,
              homepage,
              team_request_membership,
              logo,
              readme,
              delete,
              team_view,
              export,
              )

    return unittest.TestSuite(suites)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
