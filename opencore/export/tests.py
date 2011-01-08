import doctest
from opencore.featurelets.interfaces import IListenContainer
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import OpencoreContent
from opencore.testing.logtest import LoggingTestCase
import unittest
from zope.app.component.hooks import setSite
from zope.app.component.hooks import setHooks
from zope.interface import alsoProvides

optionflags = doctest.ELLIPSIS
import warnings; warnings.filterwarnings("ignore")

def test_suite():

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
        
    globs = locals()

    export = dtf.ZopeDocFileSuite("export.txt",
                                  optionflags=optionflags,
                                  package='opencore.export',
                                  test_class=LoggingTestCase,
                                  globs=globs,
                                  setUp=contents_content,
                                  layer=OpencoreContent,
                                  )
    suites = (export,)
    return unittest.TestSuite(suites)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
