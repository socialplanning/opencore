from zope.interface import implements
from zope.component import adapts

from opencore.interfaces import IOpenTeam
from opencore.interfaces.pending_requests import IRequestMembership

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

    def join(self):
        context = self.context
        joined = context.join()
        if not joined:
            return False
        # send email
        return True