import os
import unittest
from zope.testing import doctest
from Testing.ZopeTestCase import FunctionalDocFileSuite
from opencore.testing.layer import OpencoreContent as test_layer
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase

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
    from opencore.nui.member.interfaces import ITransientMessage
    from opencore.nui.project.interfaces import IEmailInvites

    img = os.path.join(os.path.dirname(__file__), 'test-portrait.jpg')
    portrait = open(img)

    globs = locals()
    readme = FunctionalDocFileSuite("README.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui.member',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    )

    readme.layer = test_layer
    pending = FunctionalDocFileSuite("pending_requests.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui.member',
                                    test_class=OpenPlansTestCase,
                                    globs = globs,
                                    )

    pending.layer = test_layer

    transient = FunctionalDocFileSuite('transient-message.txt',
                                 optionflags=optionflags,
                                 package='opencore.nui.member',
                                 test_class=OpenPlansTestCase,
                                 globs=globs,
                                 )

    return unittest.TestSuite((readme, transient, pending))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
