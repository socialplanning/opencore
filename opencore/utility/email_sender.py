from zope.component import implements
from zope.i18nmessageid import Message

class EmailSender(object):
    """
    A thing that sends email. Based on opencore.nui.email_sender.EmailSender
    but somewhat less dependent on opencore.nui views.
    """
    implements(IEmailSender)

    def constructMailMessage(self, msg_id, **kwargs):
        if not kwargs.has_key('portal_title'):
            kwargs['portal_title'] = self.portal_title #XX
        msg = getattr(self.messages, msg_id) #XX
        unicode_kwargs = self._unicode_values(kwargs) #XX
        msg = Message(msg, mapping=unicode_kwargs)
        
