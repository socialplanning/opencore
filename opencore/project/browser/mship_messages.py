from opencore.i18n import _

invite_member = _(
    u'email_invite_member',
    u"""Hi ${user_name},

You have been invited to join "${project_title}" by ${inviter_name}.
Please visit your account page to accept or decline the invitation: ${account_url}

Cheers,
The ${portal_name} Team
${portal_url}
""")

invite_member_subject = _(
    u'email_invite_member_subject',
    u"""You've been invited to join "${project_title}" """)

invite_pending_member = _(
    u'email_invite_pending_member',
    u"""Hi ${user_name},

You have been invited to join "${project_title}" by ${inviter_name}.
Please first confirm your email address at the following address: ${conf_url}
and then you can accept or decline the invitation.

Cheers,
The ${portal_name} Team
${portal_url}
""")

invite_pending_member_subject = _(
    u'email_invite_pending_member_subject',
    u"""You've been invited to join ${project_title}"""
    )

remind_invitee = _(
    u'email_remind_invitee', 
    u"""
This is a reminder that you've been invited to join "${project_title}" on ${portal_title}.
Please visit your account page to accept or decline the invitation: ${account_url}
""")

remind_invitee_subject = _(
    u'email_remind_invitee_subject',
    u""" ${portal_title} - Invitation to join ${project_title} """
    )

remind_pending_invitee = _(
    u'email_remind_pending_invitee',
    u"""
This is a reminder that you've been invited to join "${project_title}" on ${portal_title}.
Please first confirm your email address at the following address: ${conf_url}
and then you can accept or decline the invitation.
""")

remind_pending_invitee_subject = _(
    u'email_remind_pending_invitee_subject',
    u"${portal_title} - Invitation to join ${project_title}"
    )

request_approved = _(
    u'email_request_approved', 
    u"""
Your request to join "${project_title}" on ${portal_title} has been approved.
The ${project_noun} is accessible at the following address:

${project_url}
""")

request_approved_subject = _(
    u'email_request_approved_subject', 
    u"${portal_title} - Welcome to ${project_title}"
    )

request_denied = _(
    u'email_request_denied',
    u"""
Your request to join "${project_title}" on ${portal_title} has been denied.
""")

request_denied_subject = _(
    u'email_request_denied_subject',
    u"${portal_title} - Your request to join ${project_title}"
    )

invitation_retracted = _(
    u'email_invitation_retracted',
    u"""
The invitation extended to you to join "${project_title}" on ${portal_title} has been revoked.
""")

invitation_retracted_subject = _(
    u'email_invitation_retracted_subject',
    u"""${portal_title} - Invitation to join  ${project_title}""")

membership_deactivated = _(
    u'email_membership_deactivated', 
    u"""
You are no longer a member of "${project_title}" on ${portal_title}.
""")

membership_deactivated_subject = _(
    u'email_membership_deactivated_subject', 
    u"${portal_title} - Membership deactivated for ${project_title}"
    )

email_invite_static_body = _(u'email_invite_static_body')
