from Acquisition import aq_inner
from zope.interface import implements
from zope.component import adapts

from Products.CMFCore.utils import getToolByName
from Products.MailHost.MailHost import MailHostError

from topp.utils.detag import detag
from opencore.i18n import _
from opencore.interfaces import IOpenTeam
from opencore.interfaces import IOpenSiteRoot
from opencore.interfaces.pending_requests import IRequestMembership
from opencore.project.utils import project_noun
from opencore.utility.interfaces import IEmailSender
from opencore.utils import interface_in_aq_chain

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
        self.portal = interface_in_aq_chain(aq_inner(context), IOpenSiteRoot)

    # XXX kill
    @property
    def _loggedinmember(self):
        membertool = getToolByName(self.portal, "portal_membership")
        return membertool.getAuthenticatedMember()

    # XXX kill
    def _construct_request_email(self, request_message=None):
        team = self.context
        team_manage_url = "%s/projects/%s/manage-team" % (self.portal.absolute_url(), team.id)
        member = self._loggedinmember
        member_string = member.getId()
        member_fn = member.getFullname()
        if member_fn:
            member_string = member_string + ' (' + member_fn + ')'
        email_msg = _(u'email_membership_requested',
                      mapping = {'member_id': member_string,
                                 'project_title': team.title,
                                 'project_noun': project_noun(),
                                 'team_manage_url': team_manage_url,
                                 }
                      )
        
        sender = IEmailSender(self.portal)
        email_msg = sender.constructMailMessage(email_msg)

        if request_message:
            member_message = _('email_mship_request_message',
                               mapping = {'member_id': member_string,
                                          'project_title': team.title,
                                          'team_manage_url': team_manage_url,
                                          'member_message': detag(request_message),
                                          }
                               )
            member_message = sender.constructMailMessage(member_message)
            email_msg += member_message
        return email_msg
        
    def join(self, request_message=None):
        context = self.context
        joined = context.join()
        if not joined:
            return False

        sender = IEmailSender(self.portal)
        email_msg = self._construct_request_email(request_message)
        mto = context.get_admin_ids()
        for recipient in mto:
            try:
                sender.sendMail(recipient, msg=email_msg)
            except MailHostError:
                pass

        return True
