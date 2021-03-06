from Products.validation.validators.BaseValidators import EMAIL_RE
from plone.mail import construct_simple_encoded_message
from types import StringTypes
from zope.i18nmessageid import Message
import re

regex = re.compile(EMAIL_RE)


class EmailSender(object):
    """
    Encapsulates the email message sending logic for the OpenPlans NUI
    user interface.  Needs to be passed an instance of a BaseView
    subclass at creation time.
    """
    def __init__(self, view, messages=None, secureSend=False):
        """
        o view: an instance of a BaseView subclass that provides a
        mechanism for the EmailSender to access tools and the Zope
        object tree

        o messages: an object (usually a python module) that contains
        attributes corresponding to the email messages to go out.

        o secureSend: whether we should attempt to use the secureSend
        vs. the send function
        """
        # XXX This implementation has encoding bugs.
        # Let's kill it and use the opencore.utility version instead,
        # which seems to work better.
        # I'd like to add a DeprecationWarning, but not until we've
        # removed all usage of this from opencore itself.
#         import warnings
#         warnings.warn(DeprecationWarning(
#                 "opencore.nui.email_sender should not be used; "
#                 "use IEmailSender from opencore.utility instead"))
        self.view = view
        self.messages = messages
        self.secureSend = secureSend

    @property
    def mailhost(self):
        # getToolByName(self.context, "MailHost")
        return self.view.get_tool('MailHost') 

    @property
    def send(self):
        return (self.secureSend
                 and self.mailhost.secureSend
                 or self.mailhost.send)

    def toEmailAddress(self, addr_token):
        """
        Returns the appropriate email address for a given token.

        o token: must be either an email address or a member id; if an
        address is provided, it will be returned unchanged.  if not,
        then it will be assumed to be a member id and the member's
        address will be returned (including member fullname, if it
        exists).
        """
        addr_token = addr_token.strip().lstrip('<').rstrip('>')
        if not addr_token:
            return None
        view = self.view
        if regex.match(addr_token) is None:
            # not an address, it should be a member id
            # getToolByName(self.context, "portal_membership")
            member = view.membertool.getMemberById(addr_token)

            # member.getEmail()
            member_info = view.member_info_for_member(member)
            email_string = member_info.get('email')
            fullname = member_info.get('fullname')
            if fullname:
                # XXX: work around aggressive SecureMailHost validation
                fullname = fullname.split(',')[0]
                email_string = '%s <%s>' % (fullname, email_string)
            return email_string
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

    def constructMailMessage(self, msg_id, **kwargs):
        """
        Retrieves and returns the mail message text from the
        mship_messages module that is in the same package as this
        module.

        o msg_id: the name of the message that is to be retrieved

        o **kwargs: should be a set of key:value pairs that can be
        substituted into the desired message.  extraneous kwargs will
        be ignored; failing to include a kwarg required by the
        specified message will raise a KeyError.
        """
        # insert the portal title, used by nearly every message
        if not kwargs.has_key('portal_title'):
            kwargs['portal_title'] = self.view.portal_title() # needs to go
        msg = getattr(self.messages, msg_id)
        unicode_kwargs = self._unicode_values(kwargs)
        msg = Message(msg, mapping=unicode_kwargs)
        return self.view.translate(msg) # needs to go

    def sendEmail(self, mto, msg=None, msg_id=None, subject=None,
                  mfrom=None, **kwargs):
        """
        Sends an email.

        o mto: the message recipient.  either an email address or a
        member id, or a sequence of the same.

        o msg: the message to send.  if None, then msg_id must be
        provided.

        o msg_id: the id of the message; message text should be
        available as an attribute on the 'messages' object that was
        passed in to the constructor.  if None, then msg must be
        provided.  if both are provided, msg will take precedence.

        o subject: message subject; if None it's assumed that the
        subject header will be embedded in the message text.

        o mfrom: the message sender.  either an email address or a
        member id.  if None, then the currently authenticated user
        will be used as the sender.

        o **kwargs: a set of key:value pairs that can be substituted
        into the desired message.  extraneous kwargs will be ignored,
        failing to include a kwarg required by the specified message
        will raise a KeyError.
        """
        view = self.view
        to_info = None
        if msg is None:
            msg = self.constructMailMessage(msg_id, **kwargs)
        if isinstance(msg, Message):
            # insert the portal title, used by nearly every message,
            # including those that don't come from constructMailMessage().
            # fixes bug #1711.
            msg.mapping.setdefault('portal_title', self.view.portal_title())
            msg = self.view.translate(msg)
        if isinstance(subject, Message):
            subject = self.view.translate(subject) #needs to go
        if type(mto) in StringTypes:
            mto = (mto,)
        recips = []
        for recip in mto:
            recip = self.toEmailAddress(recip)
            # prevent None's from getting added (maybe only test
            # environ case, but the admin users have no emails)
            if recip:
                recips.append(recip)

        if mfrom is None:
            mfrom = view.portal.getProperty('email_from_address') # needs to go
        else:
            mfrom = self.toEmailAddress(mfrom)

        charset = 'utf-8'
        if isinstance(msg, unicode):
            msg = msg.encode(charset)

        try:
            self.send(msg, recips, mfrom, subject, charset=charset)
        except TypeError:
            # damn those inconsistent MailHost APIs
            self.send(msg, recips, mfrom, subject, encode='8bit')
