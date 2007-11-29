"""
$Id: $
"""
import os, sys
import unittest

from cStringIO import StringIO
from Testing import ZopeTestCase
from Testing.ZopeTestCase import placeless
from zope.interface import directlyProvides, directlyProvidedBy, \
     classImplements
from zope.component import getMultiAdapter
from zope.configuration.exceptions import ConfigurationError
from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.content.folder import ATFolder

from Products.Fate.tests.utils import load_string

from opencore.interfaces.adding import IAddProject
from openplanstestcase import OpenPlansTestCase, makeContent
from sets import Set

class AddFormTest(OpenPlansTestCase):

    def afterSetUp(self):
        self.request = self.portal.REQUEST

    def test_add_project(self):
        self.loginAsPortalOwner()
        pfolder = self.portal._getOb('projects')
        view = getMultiAdapter((pfolder, self.request),
                               name='do_add_project')
        view.update()
        self.assertEqual(
            Set(view.fieldNames),
            Set(['id', 'title', 'space_teams', 'logo',
                 'location', 'position-text']))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AddFormTest))
    return suite

