from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from datetime import datetime
from opencore.browser.base import BaseView
from opencore.utility.interfaces import IEmailSender
from pprint import pformat
import os
import urlparse


class ErrorView(BaseView):

    notfound = ZopeTwoPageTemplateFile('notfound.pt')
    error = ZopeTwoPageTemplateFile('error.pt')

    # these are the portal types that can show up in the 404 search results
    notfound_portal_types = ['Document', 'Open Mailing List', 'OpenProject',
                             'FileAttachment']

    def find_name(self):
        """ this is really dumb. there must be a better way. """
        return self.request.getURL().split('/')[-1]

    def query(self):
        name = self.find_name()
        cat = getToolByName(self.context, 'portal_catalog')
        results = cat(path='/'.join(self.context.getPhysicalPath()),
                      SearchableText=name,
                      portal_type=self.notfound_portal_types)
        return results[:10]

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

        if 'SUPERVISOR_ENABLED' in os.environ:
            method = self.request.environ['REQUEST_METHOD']
            if method == "POST":
                request_args = "POST arguments: %s" % pformat(self.request.form)
            else:
                request_args = ""
            username = self.request.get('use_logged_in_user', 'anonymous')
            print """<!--XSUPERVISOR:BEGIN-->
Content-Type: text/plain
Username: %s
Request-url: %s
Method: %s

Environment: %s

%s

Traceback: %s
<!--XSUPERVISOR:END-->""" % (username, 
                             self.request.ACTUAL_URL,
                             method,
                             pformat(self.request.environ),
                             request_args,
                             self.traceback)
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
                domain = urlparse.urlparse(self.request.getURL())[1]
                if domain.startswith('www.'):
                    domain = domain[len('www.'):]
                user_email = "anonymous@%s" % domain

            msg = ('On %(time)s, %(user_email)s went to the URL %(url)s.\n\n'
                   'Did: %(did)s\n\nExpected: %(expected)s\n\nTraceback: %(traceback)s' % locals())
            site = portal.getProperty('title', 'Untitled site')
            email_sender.sendMail(mto, msg, '[%s] site error report' % site,
                                  user_email)
            self.add_status_message(u'Thanks for your feedback.')
        return self.redirect(portal.absolute_url())
