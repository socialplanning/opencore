from Products.CMFCore.utils import getToolByName
from Products.listen.lib.common import construct_simple_encoded_message
from Products.validation.validators.BaseValidators import EMAIL_RE
from opencore.i18n import i18n_domain
from opencore.i18n import translate
from opencore.interfaces import IOpenSiteRoot
from opencore.utility.interfaces import IEmailSender
from types import StringTypes
from zope.component import adapts
from zope.i18nmessageid import Message
from zope.interface import implements
from pprint import pprint
import re
import sys
from email.quopriMIME import body_encode

email_regex = re.compile(EMAIL_RE)

class EmailSender(object):
    """
    A thing that sends email. Based on opencore.nui.email_sender.EmailSender
    but somewhat less dependent on opencore.nui views.

    XXX commonalities seriously need to be factored out, this is ridiculous.
    Either that, or kill off the nui one.
    """
    implements(IEmailSender)
    adapts(IOpenSiteRoot)
    debug = False
    #debug = True    

    def __init__(self, context):
        self.context = context

    @property
    def _mailhost(self):
        return getToolByName(self.context, "MailHost")

    def debug_send(self, *args, **kw):
        pprint(locals(), sys.stderr)

    @property
    def _encoding(self):
        putils = getToolByName(self.context, 'plone_utils')
        return putils.getSiteEncoding()

    @property
    def _send(self):
        if self.debug:
            return self.debug_send
        return self._mailhost.send

    def _to_email_address(self, addr_token):
        if not addr_token:
            return None
        maybe_email = addr_token.strip()
        name = None
        if maybe_email.count('<'):
            name, maybe_email = maybe_email.split('<', 1)
            name = name.strip()
        maybe_email = maybe_email.strip('<> ')
        if email_regex.match(maybe_email) is not None:
            # It was already an email address.  Return with name if provided.
            if name:
                return '%s <%s>' % (name, maybe_email)
            else:
                return maybe_email
        else:
            # Not an address, it should be a member id.
            membertool = getToolByName(self.context, "portal_membership")
            member = membertool.getMemberById(addr_token)
            try:
                return member.getEmail()
            except:
                # we don't know what it is, return the original token and let
                # the caller sort it out
                return addr_token

    def _unicode_values(self, d):
        result = {}
        for k, v in d.items():
            if v is None:
                v = u''
            if isinstance(v, unicode):
                result[k] = v
            else:
                result[k] = unicode(v, self._encoding)
        return result

    def _translate(self, msgid, domain=i18n_domain, mapping=None,
                   target_language=None, default=None):
        # Ensure that our mapping gets used...
        if isinstance(msgid, Message):
            if msgid.mapping:
                tmp = msgid.mapping.copy()
                tmp.update(mapping or {})
                mapping = tmp
            # Messages have a read-only mapping; we can make a copy to stuff
            # our mapping in there.
            msgid = Message(msgid, mapping=mapping)
        # ... and does not contain binary encoded strings.
        mapping.update(self._unicode_values(mapping))

        kw = dict(domain=domain, mapping=mapping,
                  context=self.context,
                  target_language=target_language, default=default)
        return translate(msgid, **kw)

    def constructMailMessage(self, msg, **kwargs):
        """Construct a translated message out of a message id."""
        kwargs.setdefault('portal_title', self.context.Title())
        return self._translate(msgid=msg, mapping=kwargs)

    def sendMail(self, mto, msg=None, subject=None,
                 mfrom=None, **kwargs):
        """
        Send a message.
         mto - an email address or list of email addresses.
         msg - a message string or Message instance.
               (If you have a msgid, use constructMailMessage() first.
         subject - a subject string or Message instance.
         mfrom - the sender's email address.

         Any remaining keyword args are used for interpolation when
         translating the message.
        """
        # insert the portal title, used by nearly every message,
        # including those that don't come from constructMailMessage().
        # fixes bug #1711.
        kwargs.setdefault('portal_title', self.context.Title())
        if isinstance(msg, Message):
            msg = self._translate(msg, mapping=kwargs)
        if isinstance(subject, Message):
            subject = self._translate(subject, mapping=kwargs)
        if type(mto) in StringTypes:
            mto = (mto,)
        recips = []
        for recip in mto:
            recip = self._to_email_address(recip)
            # prevent None's from getting added (maybe only test
            # environ case, but the admin users have no emails)
            if recip:
                recips.append(recip)

        # XXX Validate that there's at least one recip??

        if mfrom is None:
            mfrom = self.context.getProperty('email_from_address')
        else:
            email_addr = self._to_email_address(mfrom)
            # if mfrom doesn't look like a valid email address
            # and is not a userid, we return none back
            # this happens for addresses like anonymous@nohost
            # which occurs during unit tests
            # we leave the mfrom alone in that case
            if email_addr is not None:
                mfrom = email_addr
        
        #we construct the mail message ourselves ... because the mailhost generates bogus messages
        #by bogus i mean that the mail message generated has 2 sets of separate headers
        mapping = self._unicode_values(dict(
            from_addr=mfrom,
            to_addr='; '.join(recips),
            subject=subject,
            body=msg,
            ))
        if subject:
            msg = u"""\
From: %(from_addr)s
To: %(to_addr)s
Subject: %(subject)s

%(body)s""" % mapping
        else:
            msg = u"""\
From: %(from_addr)s
To: %(to_addr)s
%(body)s""" % mapping

        # At this point we should have a unicode string; we need raw
        # bytes to send, and we need to do the weird quoted-printable
        # encoding of non-ascii strings.
        try:
            msg = msg.encode('ascii')
        except UnicodeEncodeError:
            mapping['encoding'] = self._encoding

            # see http://trac.openplans.org/openplans/ticket/2808
            # it looks like construct_simple_encoded_message ought
            # to be doing this itself, but the line is commented
            # out there, so i'll be cautious and make the most
            # minimally-invasive change possible. this should
            # probably be investigated upstream in listen and
            # (hopefully) this line eventually removed.
            mapping['body'] = body_encode(mapping['body'])

            msg = str(construct_simple_encoded_message(**mapping))

        self._send(msg)
