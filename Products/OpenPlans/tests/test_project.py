import os, sys
import unittest

from Products.Archetypes.Field import Image
from Products.CMFCore.utils import getToolByName
from openplanstestcase import OpenPlansTestCase, makeContent

class TestOpenProject(OpenPlansTestCase):

    def afterSetUp(self):

        # make some test content
        mstool = getToolByName(self.portal, 'portal_membership')
        self.loginAsPortalOwner()
        mstool.getAuthenticatedMember() # wrap user
        self.proj = makeContent(self.folder, 'project1', 'OpenProject')

    def test_addProject(self):
        self.failUnless(self.proj != None)

    def test_logo(self):
        img = os.path.join(os.path.dirname(__file__), 'test-logo.jpg')
        logo = open(img)
        self.proj.setLogo(logo)
        assert isinstance(self.proj.restrictedTraverse('logo_thumb'), Image)
        for square_name in 'square_thumb', 'square_fifty_thumb':
            image = self.proj.restrictedTraverse('logo_%s' % square_name)
            assert isinstance(image, Image)
            assert image.width == image.height

    def test_history(self):
        """
        tests history and versions using CMFEditions
        """

        self.loginAsPortalOwner()

        # get the history of the content
        portal_repository = getToolByName(self.portal, 'portal_repository')
        pageid = getattr(self.proj, 
                         self.proj.invokeFactory("Document", "foo"))
        history = portal_repository.getHistory(self.proj, 'foo')

        self.failIf(history) # no history yet

        pageid.title=u'Fleem'
        portal_repository.save(obj=pageid, comment='bar')

        history = portal_repository.getHistory(pageid)
        self.failUnless(len(history) == 1)
        lc = [i for i in history]

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestOpenProject))
    return suite

