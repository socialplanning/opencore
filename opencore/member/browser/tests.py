import os
import unittest
from zope.testing import doctest
from Testing.ZopeTestCase import FunctionalDocFileSuite
from opencore.testing.layer import MockHTTPWithContent as test_layer
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from opencore.testing import dtfactory as dtf

#optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

def test_suite():
    # these imports are needed inside the doctests
    from Products.CMFCore.utils import getToolByName
    from zope.interface import alsoProvides
    from zope.component import getUtility
    from opencore.interfaces import IMemberFolder
    from opencore.interfaces.pending_requests import IPendingRequests
    from opencore.interfaces.message import ITransientMessage
    from opencore.interfaces.membership import IEmailInvites

    img = os.path.join(os.path.dirname(__file__), 'test-portrait.jpg')
    portrait = open(img)

    globs = locals()
    readme = dtf.ZopeDocFileSuite("README.txt",
                                    optionflags=optionflags,
                                    package='opencore.member.browser',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    layer = test_layer
                                    )


    return unittest.TestSuite((readme,))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
