from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.CMFCore.utils import getToolByName

from opencore.browser.base import BaseView
from opencore.utility.interfaces import IEmailSender
from datetime import datetime

class ErrorView(BaseView):

    notfound = ZopeTwoPageTemplateFile('notfound.pt')
    error = ZopeTwoPageTemplateFile('error.pt')

    def find_name(self):
        """ this is really dumb. there must be a better way. """
        return self.request.getURL().split('/')[-1]

    def query(self):
        name = self.find_name()
        cat = getToolByName(self.context, 'portal_catalog')
        results = cat(path='/'.join(self.context.getPhysicalPath()), SearchableText=name)
        return results

    def user_email(self):
        membertool = getToolByName(self.context, 'portal_membership')
        if membertool.isAnonymousUser():
            return ''
        return membertool.getAuthenticatedMember().getEmail()

    def submit_url(self):
        return self.portal.absolute_url() + '/submit-error-report'

    def __call__(self, *args, **kw):
        self.traceback = kw.get('error_tb', '')
        self.request_time = str(datetime.now())
        if kw['error_type'] == 'NotFound':
            return self.notfound(*args, **kw)
        return self.error(*args, **kw)

class ErrorReporter(BaseView):

    def __call__(self):
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        if 'error_submitted' in self.request.form:
            traceback = self.request.form.get('traceback', '')
            time = self.request.form.get('time', '')
            url = self.request.form.get('url', '')

            did = self.request.form.get('oc-did', '')
            expected = self.request.form.get('oc-expected', '')
            mto = portal.getProperty('email_from_address')
            email_sender = IEmailSender(portal)

            user_email = self.request.form.get('oc-user-email', '').strip()
            if not user_email:
                user_email = "anonymous@example.com"

            msg = ('On %(time)s, %(user_email)s went to the URL %(url)s.\n\n'
                   'Did: %(did)s\n\nExpected: %(expected)s\n\nTraceback: %(traceback)s' % locals())
            site = portal.getProperty('title', 'Untitled site')
            email_sender.sendMail(mto, msg, '[%s] site error report' % site,
                                  user_email)
            self.add_status_message(u'Thanks for your feedback.')
        return self.redirect(portal.absolute_url())
