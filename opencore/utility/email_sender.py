import re
from types import StringTypes

from zope.interface import implements
from zope.component import adapts
from zope.i18nmessageid import Message

from Products.CMFCore.utils import getToolByName

from Products.validation.validators.BaseValidators import EMAIL_RE
regex = re.compile(EMAIL_RE)

from opencore.i18n import translate
from opencore.i18n import i18n_domain
from opencore.interfaces import IOpenSiteRoot
from opencore.utility.interfaces import IEmailSender

from opencore.project.browser import mship_messages

class EmailSender(object):
    """
    A thing that sends email. Based on opencore.nui.email_sender.EmailSender
    but somewhat less dependent on opencore.nui views.
    """
    implements(IEmailSender)
    adapts(IOpenSiteRoot)

    def __init__(self, context):
        self.context = context
        # this is terrible but i just want to get this out for now
        # whit suggests named adapters
        self.messages = mship_messages # @.@ 

    @property
    def _mailhost(self):
        return getToolByName(self.context, "MailHost")

    @property
    def _send(self):
        return self._mailhost.send

    def _to_email_address(self, addr_token):
        if regex.match(addr_token) is None:
            # not an address, it should be a member id
            membertool = getToolByName(self.context, "portal_membership")
            member = membertool.getMemberById(addr_token)
            try:
                return member.getEmail()
            except:
                return None
        else:
            # it's already an email address
            return addr_token

    def _unicode_values(self, d):
        result = {}
        for k, v in d.items():
            if v is None:
                v = u''
            if isinstance(v, unicode):
                result[k] = v
            else:
                result[k] = unicode(v, 'utf-8')
        return result

    def _translate(self, msgid, domain=i18n_domain, mapping=None,
                   target_language=None, default=None):
        kw = dict(domain=domain, mapping=mapping, context=self.context,
                  target_language=target_language, default=default)
        return translate(msgid, **kw)

    def constructMailMessage(self, msg_id, **kwargs):
        if not kwargs.has_key('portal_title'):
            kwargs['portal_title'] = self.context.Title()
        msg = getattr(self.messages, msg_id) #XX
        unicode_kwargs = self._unicode_values(kwargs)
        msg = Message(msg, mapping=unicode_kwargs)
        return self._translate(msg)

    def sendMail(self, mto, msg=None, msg_id=None, subject=None,
                 mfrom=None, **kwargs):
        to_info = None
        if msg is None:
            msg = self.constructMailMessage(msg_id, **kwargs)
        if isinstance(msg, Message):
            # insert the portal title, used by nearly every message,
            # including those that don't come from constructMailMessage().
            # fixes bug #1711.
            msg.mapping.setdefault('portal_title', self.context.Title())
            msg = self._translate(msg)
        if isinstance(subject, Message):
            subject = self._translate(subject)
        if type(mto) in StringTypes:
            mto = (mto,)
        recips = []
        for recip in mto:
            recip = self._to_email_address(recip)
            # prevent None's from getting added (maybe only test
            # environ case, but the admin users have no emails)
            if recip:
                recips.append(recip)

        if mfrom is None:
            mfrom = self.context.getProperty('email_from_address')
        else:
            mfrom = self._to_email_address(mfrom)

        if isinstance(msg, unicode):
            msg = msg.encode('utf-8')

        self._send(msg, recips, mfrom, subject)

