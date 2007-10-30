import os, sys, unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase 
from Testing.ZopeTestCase import FunctionalDocFileSuite
from Products.PasswordResetTool.tests.test_doctests import MockMailHostTestCase

from opencore.testing.layer import OpencoreContent

optionflags = doctest.ELLIPSIS

import warnings; warnings.filterwarnings("ignore")

# ensure that email_confirmation is set to true
from App import config
cfg = config.getConfiguration().product_config.get('opencore.nui')
if cfg is None:
    cfg = {}
    config.getConfiguration().product_config['opencore.nui'] = cfg
cfg['email-confirmation'] = 'True'

# event handler used in the tests
events_fired = []
def dummy_handler(obj, event):
    events_fired.append((obj, event))

def test_suite():
    from Products.Five.utilities.marker import erase as noLongerProvides
    from Products.PloneTestCase import ptc
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from pprint import pprint
    from zope.interface import alsoProvides

    def readme_setup(tc):
        tc._refreshSkinData()
        pwt = tc.portal.portal_workflow
        member = tc.portal.portal_membership.getAuthenticatedMember()
        if pwt.getInfoFor(member, 'review_state') == 'pending':
            member.isConfirmable = True
            pwt.doActionFor(member, 'register_public')
            del member.isConfirmable

    globs = locals()
    readme = FunctionalDocFileSuite("README.txt",
                                    optionflags=optionflags,
                                    package='opencore.nui.account',
                                    test_class=MockMailHostTestCase,
                                    globs = globs,
                                    setUp=readme_setup
                                    )

    readme.layer = OpencoreContent

    return unittest.TestSuite((readme,))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
