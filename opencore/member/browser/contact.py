from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.i18n import _
from opencore.browser.formhandler import OctopoLite
from opencore.browser.formhandler import action
from opencore.utility.interfaces import IEmailSender
from opencore.member.browser.view import ProfileView

class MemberContactView(ProfileView, OctopoLite):
    """
    View class for the member contact form.
    """
    template = ZopeTwoPageTemplateFile('contact.pt')

    @property
    def referer(self):
        urltool = self.get_tool('portal_url')
        http_referer = self.request.get('HTTP_REFERER')
        if urltool.isURLInPortal(http_referer):
            return http_referer

    @action("send")
    def send(self, target=None, fields=None):
        sender = IEmailSender(self.portal)
        mto = self.viewed_member_info.get('email')
        mfrom = self.loggedinmember.getId()
        msg = self.request.form['message']
        subject = self.request.form['subject']
        sender.sendMail(mto, msg=msg, subject=subject, mfrom=mfrom)
        self.addPortalStatusMessage(_(u'psm_message_sent_to_user',
                                      u'Message sent.'))
        ret_url = self.request.form.get('ret_url') or self.context.absolute_url()
        return self.redirect(ret_url)
