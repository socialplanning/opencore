import re

from Products.validation.validators.BaseValidators import EMAIL_RE

class EmailSender(object):
    """
    Encapsulates the email message sending logic for the OpenPlans NUI
    user interface.  Needs to be passed an instance of a BaseView
    subclass at creation time.
    """
    def __init__(self, view, messages):
        """
        o view: an instance of a BaseView subclass that provides a
        mechanism for the EmailSender to access tools and the Zope
        object tree

        o messages: an object (usually a python module) that contains
        attributes corresponding to the email messages to go out
        """
        self.view = view
        self.messages = messages

    @property
    def mailhost(self):
        return self.view.get_tool('MailHost')

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
        msg = getattr(self.messages, msg_id)
        return msg % kwargs

    def sendEmail(self, mto, msg=None, msg_id=None, subject=None,
                  **kwargs):
        """
        Sends an email.  It's assumed that the currently logged in
        user is the sender.a

        o mto: the message recipient.  either an email address or a
        member id.

        o msg: the message to send.  if None, then msg_id must be
        provided.

        o msg_id: the id of the message; message text should be
        available as an attribute on the 'messages' object that was
        passed in to the constructor.  if None, then msg must be
        provided.  if both are provided, msg will take precedence.

        o subject: message subject; if None it's assumed that the
        subject header will be embedded in the message text.

        o **kwargs: a set of key:value pairs that can be substituted
        into the desired message.  extraneous kwargs will be ignored,
        failing to include a kwarg required by the specified message
        will raise a KeyError.
        """
        view = self.view
        to_info = None
        if msg is None:
            msg = self.constructMailMessage(msg_id, **kwargs)
        regex = re.compile(EMAIL_RE)
        if regex.match(mto) is None:
            to_mem = view.membertool.getMemberById(mto)
            to_info = view.member_info_for_member(to_mem)
            mto = to_info.get('email')

        mfrom = view.member_info.get('email')
        self.mailhost.send(msg, mto, mfrom, subject)

