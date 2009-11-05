from opencore.i18n import _

invite_member = _(u'email_invite_member', u"""Subject: You've been invited to join "${project_title}"

Hi ${user_name},

You have been invited to join "${project_title}" by ${inviter_name}.
Please visit your account page to accept or decline the invitation: ${account_url}

Cheers,
The ${portal_name} Team
${portal_url}
""")

invite_pending_member = _(u'email_invite_pending_member', u"""Subject: You've been invited to join "${project_title}"

Hi ${user_name},

You have been invited to join "${project_title}" by ${inviter_name}.
Please first confirm your email address at the following address: ${conf_url}
and then you can accept or decline the invitation.

Cheers,
The ${portal_name} Team
${portal_url}
""")

remind_invitee = _(u'email_remind_invitee', u"""Subject: ${portal_title} - Invitation to join ${project_title}

This is a reminder that you've been invited to join "${project_title}" on ${portal_title}.
Please visit your account page to accept or decline the invitation: ${account_url}
""")

remind_pending_invitee = _(u'email_remind_pending_invitee', u"""Subject: ${portal_title} - Invitation to join ${project_title}

This is a reminder that you've been invited to join "${project_title}" on ${portal_title}.
Please first confirm your email address at the following address: ${conf_url}
and then you can accept or decline the invitation.
""")

request_approved = _(u'email_request_approved', u"""Subject: ${portal_title} - Welcome to ${project_title}

Your request to join "${project_title}" on ${portal_title} has been approved.  The ${project_noun} is accessible at the following address: ${project_url}
""")

request_denied = _(u'email_request_denied', u"""Subject: ${portal_title} - Your request to join ${project_title}

Your request to join "${project_title}" on ${portal_title} has been denied.
""")

invitation_retracted = _(
    u'email_invitation_retracted',
    u"""
The invitation extended to you to join "${project_title}" on ${portal_title} has been revoked.
""")

invitation_retracted_subject = _(
    u'email_invitation_retracted_subject',
    u"""${portal_title} - Invitation to join  ${project_title}""")

membership_deactivated = _(u'email_membership_deactivated', u"""Subject: ${portal_title} - Membership deactivated for ${project_title}

You are no longer a member of "${project_title}" on ${portal_title}.
""")

email_invite_static_body = _(u'email_invite_static_body')
