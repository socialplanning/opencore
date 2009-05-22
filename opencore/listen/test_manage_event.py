from Products.CMFPlone.utils import _createObjectByType
from Products.MailHost.interfaces import IMailHost
from Products.OpenPlans.tests.openplanstestcase import OpenPlansTestCase
from Products.listen.interfaces import IListLookup
from zope.component import getMultiAdapter
from zope.component import getUtility

class TestMailingListManageEvent(OpenPlansTestCase):

    """test to exercise the manage_event function called from smtp2zope on
       errors"""

    def afterSetUp(self):
        """create a mailing list that we can send events to"""
        oc_props = self.portal.portal_properties.opencore_properties
        self._old_fqdn = oc_props.getProperty('mailing_list_fqdn')
        oc_props.manage_changeProperties(mailing_list_fqdn='lists.example.org')
        ml = _createObjectByType('Open Mailing List', self.portal, 'mylist')
        ml.setTitle('My List')
        ml.mailto = 'mylist'
        ll = getUtility(IListLookup)
        ll.registerList(ml)
        self.mailhost = getUtility(IMailHost)


    def beforeTearDown(self):
        self.mailhost.messages = []
        oc_props = self.portal.portal_properties.opencore_properties
        oc_props.manage_changeProperties(mailing_list_fqdn=self._old_fqdn)


    def _getView(self):
        return getMultiAdapter((self.portal, self.portal.REQUEST),
                               name='manage_event')

    def test_200_error(self):
        view = self._getView()
        # XXX HARDCODED DOMAIN
        headers = {'from': 'johnnywalker@example.com',
                   'to': 'mylist@lists.example.org',
                   }
        status_codes = [200]
        view(status_codes, headers)
        msgs = self.mailhost.messages
        self.assertEqual(1, len(msgs), 'No error message sent')
        msg = msgs[0]
        # XXX HARDCODED DOMAIN
        self.assertEqual('mylist-manager@lists.example.org', msg['mfrom'])
        self.assertEqual(['johnnywalker@example.com'], msg['mto'])
        self.assertEqual('Mailing list error: message too big',  msg['subject'])
        self.failUnless("message that you're trying to send is too big" in msg['msg'])

    def test_default_error(self):
        view = self._getView()
        # XXX HARDCODED DOMAIN
        headers = {'from': 'mister.dewars@example.com',
                   'to': 'mylist@lists.example.org',
                   }
        # any unknown status code
        status_codes = [777]
        view(status_codes, headers)
        msgs = self.mailhost.messages
        self.assertEqual(1, len(msgs), 'No error message sent')
        msg = msgs[0]
        # XXX HARDCODED DOMAIN
        self.assertEqual('mylist-manager@lists.example.org', msg['mfrom'])
        self.assertEqual(['mister.dewars@example.com'], msg['mto'])
        self.assertEqual('Mailing list error', msg['subject'])
        self.failUnless('unknown error' in msg['msg'])
