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
        ml = _createObjectByType('Open Mailing List', self.portal, 'mylist')
        ml.setTitle('My List')
        ml.mailto = 'mylist'
        ll = getUtility(IListLookup)
        ll.registerList(ml)

    def _getView(self):
        return getMultiAdapter((self.portal, self.portal.REQUEST),
                               name='manage_event')

    def test_200_error(self):
        view = self._getView()
        headers = {'from': 'johnnywalker@example.com',
                   'to': 'mylist@lists.openplans.org',
                   }
        status_codes = [200]
        view(status_codes, headers)
        mailhost = getUtility(IMailHost)
        msgs = mailhost.messages
        self.assertEqual(1, len(msgs), 'No error message sent')
        msg = msgs[0]
        self.assertEqual('mylist-manager@lists.openplans.org', msg['mfrom'])
        self.assertEqual(['johnnywalker@example.com'], msg['mto'])
        self.assertEqual('Mailing list error: message too big',  msg['subject'])
        self.failUnless("message that you're trying to send is too big" in msg['msg'])

    def test_default_error(self):
        view = self._getView()
        headers = {'from': 'mister.dewars@example.com',
                   'to': 'mylist@lists.openplans.org',
                   }
        # any unknown status code
        status_codes = [777]
        import pdb; pdb.set_trace()
        view(status_codes, headers)
        mailhost = getUtility(IMailHost)
        msgs = mailhost.messages
        self.assertEqual(1, len(msgs), 'No error message sent')
        msg = msgs[0]
        self.assertEqual('mylist-manager@lists.openplans.org', msg['mfrom'])
        self.assertEqual(['mister.dewars@example.com'], msg['mto'])
        self.failUnless('Subject: Mailing list error' in msg['msg'])
        self.failUnless('unknown error' in msg['msg'])
