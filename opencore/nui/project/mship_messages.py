from opencore.i18n import _

# @@ could we use some fricking type of templates here?

invite_member = _(u'email_invite_member', u"""Subject: ${portal_title} - Invitation to join ${project_title}

You have been invited to join "${project_title}".  Please visit your account page to accept or decline the invitation: ${account_url}
""")

remind_invitee = _(u'email_remind_invitee', u"""Subject: ${portal_title} - Invitation to join ${project_title}

This is a reminder that you've been invited to join "${project_title}" on ${portal_title}.  Please visit your account page to accept or decline the invitation: ${account_url}
""")

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

membership_requested = _(u'email_membership_requested', u"""Subject: ${portal_title} - Request to join ${project_title}

${member_id} would like to get involved with "${project_title}".

To approve or deny this request please visit the project's team management screen: ${team_manage_url}
""")

mship_request_message = _(u'email_mship_request_message', u"""

${member_id} included the following message:

"${member_message}"
""")

invite_email = _(u'email_invite_email', u"""Subject: ${portal_title} - Invitation to join ${project_title}

You have been invited to join "${project_title}" on ${portal_title}.

If you would like to get involved, set up an ${portal_title} account: ${join_url}

${portal_title} is a free toolset for social change. With ${portal_title}, you can build collaborative pages for organizing projects. You can also blog, set up mailing lists, store and share files, and keep track of tasks.

We hope you'll take ${portal_title} for a spin.

Cheers,
The ${portal_title} Team
${portal_url}
""")
