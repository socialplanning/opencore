##############################################################################
#
# Signed Cookie Auth
# Copyright 2007 The Open Planning Project
# 
# based on
# PlonePAS - Adapt PluggableAuthService for use in Plone
# Copyright (C) 2005 Enfold Systems, Kapil Thangavelu, et al
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id: test_doctests.py 32811 2006-11-06 14:01:12Z shh42 $
"""

# Load fixture
import unittest
from Testing import ZopeTestCase
from opencore.testing.layer import OpenPlansLayer
from opencore.testing.layer import MockHTTP
from opencore.testing.layer import OpenCoreContent
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
from Products.PloneTestCase.PloneTestCase import setupPloneSite

from zExceptions.ExceptionFormatter import format_exception
from ZPublisher.HTTPResponse import HTTPResponse
from Testing.ZopeTestCase import installProduct
import doctest

memxml = """
<member id="foo">
  <email>none@nothing.com</email>
  <fullname>Foo Barsky</fullname>
</member>
"""

setupPloneSite()

class MockHTTPContentLayer(MockHTTP, OpenCoreContent):
    """
    Replaces the IHTTPClient utility and creates the test content.
    """

# Silence Plone's handling of exceptions
orig_exception = HTTPResponse.exception
def exception(self, **kw):
    def tag_search(*args):
        return False
    kw['tag_search'] = tag_search
    return orig_exception(self, **kw)

orig_setBody = HTTPResponse.setBody
def setBody(self, *args, **kw):
    kw['is_error'] = 0
    if len(args[0]) == 2:
        title, body = args[0]
        args = (body,) + args[1:]
    return orig_setBody(self, *args, **kw)

def _traceback(self, t, v, tb, as_html=1):
    return ''.join(format_exception(t, v, tb, as_html=as_html))

HTTPResponse._error_format = 'text/plain'
HTTPResponse._traceback = _traceback
HTTPResponse.exception = exception
HTTPResponse.setBody = setBody

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    suite = unittest.TestSuite()
    DocFileSuite = ZopeTestCase.FunctionalDocFileSuite
    tests = (
        ('auth.txt', FunctionalTestCase, OpenPlansLayer),
        ('remote_auth.txt', FunctionalTestCase, MockHTTPContentLayer),
        )

    for fname, klass, layer in tests:
        t = DocFileSuite(fname,
                         test_class=klass,
                         optionflags = doctest.ELLIPSIS,
                         package='opencore.auth.tests')
        #all openplans tests need this
        t.layer = layer
        suite.addTest(t)
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
