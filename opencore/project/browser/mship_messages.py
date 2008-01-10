from opencore.i18n import _

invite_member = _(u'email_invite_member')

remind_invitee = _(u'email_remind_invitee')

request_approved = _(u'email_request_approved', u"""Subject: ${portal_title} - Welcome to ${project_title}

Your request to join "${project_title}" on ${portal_title} has been approved.  The project is accessible at the following address: ${project_url}
""")

request_denied = _(u'email_request_denied', u"""Subject: ${portal_title} - Your request to join ${project_title}

Your request to join "${project_title}" on ${portal_title} has been denied.
""")

invitation_retracted = _(u'email_invitation_retracted', u"""Subject: ${portal_title} - Invitation to join  ${project_title}

The invitation extended to you to join "${project_title}" on ${portal_title} has been revoked.
""")

membership_deactivated = _(u'email_membership_deactivated', u"""Subject: ${portal_title} - Membership deactivated for ${project_title}

You are no longer a member of "${project_title}" on ${portal_title}.
""")

email_invite_static_body = _(u'email_invite_static_body')
