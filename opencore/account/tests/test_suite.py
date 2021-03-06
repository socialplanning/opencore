from Products.membrane.plugins.userfactory import MembraneUser
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from opencore.account.utils import turn_confirmation_on
from opencore.member.interfaces import IHandleMemberWorkflow
from opencore.testing import dtfactory as dtf
from opencore.testing.layer import OpencoreContent, OpencoreContent
from zope.app.component.hooks import setSite
from zope.interface import implements
from zope.testing import doctest
import unittest

#import warnings; warnings.filterwarnings("ignore")

turn_confirmation_on() # should maybe go in the layer

optionflags = doctest.ELLIPSIS
 
class StubMemberWorkflow:
    """A stub to avoid depending on real members in some account tests.
    XXX Not sure where this should live? Move it if you have an idea.
    @@ maybe in opencore.testing???
    """

    implements(IHandleMemberWorkflow)

    def __init__(self, id, confirmed=False):
        self.confirmed = confirmed
        self.id = id

    def is_unconfirmed(self):
        return not self.confirmed

    def confirm(self):
        self.confirmed = True

    def getId(self):
        return self.id

def stub_getUserById(self, member_id):
    """
    used to temporarily monkeypatch PAS
    """
    return MembraneUser(member_id).__of__(self)

def normalize_whitespace(astring):
    # just a little helper to avoid caring about indentation.
    return '\n'.join([li.strip() for li in astring.split('\n')]).strip()

def readme_setup(tc):
    setSite(tc.portal)
    tc._refreshSkinData()
    tc.homepage = getattr(tc.portal, 'site-home')
    tc.request = tc.app.REQUEST
    member = tc.portal.portal_membership.getAuthenticatedMember()
    member.update(email='testuser1@example.com')
    member = IHandleMemberWorkflow(member)
    if member.is_unconfirmed():
        member.confirm()
    setSite(tc.portal)


def test_suite():
    from Products.PloneTestCase import ptc, setup
    from Testing.ZopeTestCase import FunctionalDocFileSuite, installProduct
    from pprint import pprint
    from zope.interface import alsoProvides
    from opencore.testing.utils import clear_status_messages
    from opencore.testing.utils import get_status_messages
    from opencore.utility.interfaces import IProvideSiteConfig
    from opencore.interfaces.membership import IEmailInvites
    from opencore.interfaces.member import IMemberHomePage, IMemberFolder
    from opencore.member.interfaces import IHandleMemberWorkflow
    from zope.app.component.hooks import setSite, setHooks
    from zope.component import getUtility
    from pprint import pprint

    fired = []
    setup.setupPloneSite()

    globs = locals()
    globs.update({'StubMemberWorkflow': StubMemberWorkflow,
                  'normalize_whitespace': normalize_whitespace,
                  'stub_getUserById': stub_getUserById})

    account = dtf.ZopeDocTestSuite("opencore.account.tests.account",
                                  optionflags=optionflags,
                                  test_class=OpenPlansTestCase,
                                  globs = globs,
                                  setUp=readme_setup,
                                  layer=OpencoreContent
                                  )
    invite = dtf.ZopeDocTestSuite("opencore.account.tests.invite_join",
                                  optionflags=optionflags,
                                  test_class=OpenPlansTestCase,
                                  globs = globs,
                                  setUp=readme_setup,
                                  layer=OpencoreContent
                                  )
    

    confirm = dtf.ZopeDocTestSuite("opencore.account.tests.confirm",
                                   optionflags=optionflags,
                                   test_class=ptc.PloneTestCase,
                                   globs=globs,
                                   setUp=readme_setup,
                                   layer=OpencoreContent,
                                   )

    first_login = dtf.ZopeDocTestSuite("opencore.account.tests.first_login",
                                       optionflags=optionflags,
                                       test_class=ptc.PloneTestCase,
                                       globs = globs,
                                       setUp=readme_setup,
                                       layer = OpencoreContent
                                       )

    return unittest.TestSuite((account, invite, confirm, first_login))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
