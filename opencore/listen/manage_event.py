from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.listen.interfaces import IListLookup
from rfc822 import AddressList
from zope.app.component.hooks import setSite
from zope.component import getUtility
import os

class ManageMailboxerEvents(BrowserView):

    def __call__(self, events=None, headers=None):
        if events is None or headers is None:
            return
        address = headers.get('x-original-to', None)
        if address is None:
            address = headers.get('to', None)
            if address is None:
                print 'manage_event: no address found in headers: %s' % headers
                return

        ll = getUtility(IListLookup)

        address_list = AddressList(address)
        for ml_address in address_list:
            ml = ll.getListForAddress(ml_address[1])
            if ml is not None:
                break
        else:
            print 'manage_event: no list found for address: %s' % address
            return

        setSite(ml)
        return ml.manage_event(events, headers)


class EventTemplateSender(BrowserView):

    manage_events_templates_dir = 'manage_events_templates'
    template_path = os.path.join(os.path.dirname(__file__),
                                 manage_events_templates_dir)

    template = None
    default_template_path = os.path.join(template_path,
                                         'mail_event_default.pt')

    def __call__(self, event_code, headers):
        try:
            path = os.path.join(self.template_path,
                                'mail_event_%s.pt' % event_code)
            self.template = ViewPageTemplateFile(path)
        except ValueError:
            # a ValueError gets raised if the template location is not found
            self.template = ViewPageTemplateFile(self.default_template_path)

        return self.template()
