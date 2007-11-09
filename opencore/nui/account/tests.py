from Products.PasswordResetTool.tests.test_doctests import MockMailHostTestCase
from Testing import ZopeTestCase
from Testing.ZopeTestCase import FunctionalDocFileSuite
from Testing.ZopeTestCase import PortalTestCase 
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import MockHTTPWithContent
from zope.testing import doctest
import os
import sys
import unittest
from opencore.member.interfaces import IHandleMemberWorkflow

#import warnings; warnings.filterwarnings("ignore")

from opencore.nui.account.utils import email_confirmation, turn_confirmation_on
turn_confirmation_on()

optionflags = doctest.ELLIPSIS

# event handler used in the tests
events_fired = []
def dummy_handler(obj, event):
    events_fired.append((obj, event))

def test_suite():
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import ptc
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from pprint import pprint
    from opencore.testing import alsoProvides, noLongerProvides
    from opencore.interfaces.membership import IEmailInvites
    from zope.app.component.hooks import setSite, setHooks
    from zope.component import getUtility
    import pdb
    from pprint import pprint
    globs = locals()

    def readme_setup(tc):
        setSite(tc.portal)
        tc._refreshSkinData()
        member = tc.portal.portal_membership.getAuthenticatedMember()
        member = IHandleMemberWorkflow(member)
        if member.is_unconfirmed():
            member.confirm()

    readme = dtf.ZopeDocFileSuite("README.txt",
                                        optionflags=optionflags,
                                        package='opencore.nui.account',
                                        test_class=MockMailHostTestCase,
                                        globs = globs,
                                        setUp=readme_setup,
                                        layer=MockHTTPWithContent
                                        )

    invite = dtf.ZopeDocFileSuite("invite-join.txt",
                                  optionflags=optionflags,
                                  package='opencore.nui.account',
                                  test_class=MockMailHostTestCase,
                                  globs = globs,
                                  setUp=readme_setup,
                                  layer=MockHTTPWithContent
                                  )

    return unittest.TestSuite((readme, invite))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
