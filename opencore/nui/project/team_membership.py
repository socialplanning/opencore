from Acquisition import aq_parent
from zope.interface import implements
from zope.component import adapts

from opencore.interfaces import IOpenTeam
from opencore.interfaces import IOpenSiteRoot
from opencore.interfaces.pending_requests import IRequestMembership
from opencore.utility.interfaces import IEmailSender

class RequestMembershipWithEmail(object):
    """
    IRequestMembership implementation which allows the loggedin user
    to request membership to a team.  This will create a membership
    in the pending state and send an email to the project admins.
    """
    adapts(IOpenTeam)
    implements(IRequestMembership)

    def __init__(self, context):
        self.context = context
        portal = context
        
        # XXX this is no good at all
        while portal is not None:
            portal = aq_parent(portal)
            if IOpenSiteRoot.providedBy(portal):
                break
        self.portal = portal

    def join(self):
        context = self.context
        joined = context.join()
        if not joined:
            return False
        email_sender = IEmailSender(self.portal)
        #email_sender.sendMail()
        return True
