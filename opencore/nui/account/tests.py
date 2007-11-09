from Products.PasswordResetTool.tests.test_doctests import MockMailHostTestCase
from Testing import ZopeTestCase
from Testing.ZopeTestCase import FunctionalDocFileSuite
from Testing.ZopeTestCase import PortalTestCase 
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import MockHTTPWithContent, OpencoreContent
from zope.testing import doctest
import os
import sys
import unittest

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
        pwt = tc.portal.portal_workflow
        member = tc.portal.portal_membership.getAuthenticatedMember()
        if pwt.getInfoFor(member, 'review_state') == 'pending':
            member.isConfirmable = True
            pwt.doActionFor(member, 'register_public')
            del member.isConfirmable


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
    
    first_login = dtf.ZopeDocFileSuite("firstlogin.txt",
                                       optionflags=optionflags,
                                       package='opencore.nui.account',
                                       test_class=ptc.PloneTestCase,
                                       globs = globs,
                                       setUp=readme_setup,
                                       layer = OpencoreContent
                                       )

    return unittest.TestSuite((readme, invite, first_login))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
