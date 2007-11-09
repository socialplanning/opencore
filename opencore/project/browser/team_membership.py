from Acquisition import aq_parent
from Acquisition import aq_inner
from zope.interface import implements
from zope.component import adapts

from Products.CMFCore.utils import getToolByName
from Products.MailHost.MailHost import MailHostError

from topp.utils.detag import detag
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
        portal = aq_inner(context)
        
        # XXX this is no good at all
        while portal is not None:
            portal = aq_parent(portal)
            if IOpenSiteRoot.providedBy(portal):
                break
        self.portal = portal

    # XXX kill
    @property
    def _loggedinmember(self):
        membertool = getToolByName(self.portal, "portal_membership")
        return membertool.getAuthenticatedMember()

    # XXX kill
    def _construct_request_email(self, request_message=None):
        team = self.context
        team_manage_url = "%s/projects/%s/manage-team" % (self.portal.absolute_url(), team.title)
        member = self._loggedinmember
        member_string = member.getId()
        member_fn = member.getFullname()
        if member_fn:
            member_string = member_string + ' (' + member_fn + ')'
        email_vars = {'member_id': member_string,
                      'project_title': team.title,
                      'team_manage_url': team_manage_url,
                      }

        sender = IEmailSender(self.portal)
        email_msg = sender.constructMailMessage('membership_requested',
                                                **email_vars)
        if request_message:
            email_vars.update(member_message=detag(request_message))
            email_msg += sender.constructMailMessage('mship_request_message', **email_vars)
        return (email_msg, email_vars)
        
    def join(self, request_message=None):
        context = self.context
        joined = context.join()
        if not joined:
            return False

        sender = IEmailSender(self.portal)
        email_msg, email_vars = self._construct_request_email(request_message)
        mto = context.get_admin_ids()
        for recipient in mto:
            try:
                sender.sendMail(recipient, msg=email_msg, **email_vars)
            except MailHostError:
                pass

        return True
