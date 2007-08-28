from opencore.i18n import _

invite_member = _(u"""Subject: OpenPlans - Invitation to join ${project_title}

You have been invited to join "${project_title}".  Please visit your account page to accept or decline the invitation: ${account_url}
""")

remind_invitee = _(u"""Subject: OpenPlans - Invitation to join ${project_title}

This is a reminder that you've been invited to join "${project_title}" on OpenPlans.  Please visit your account page to accept or decline the invitation: ${account_url}
""")

request_approved = _(u"""Subject: OpenPlans - Welcome to ${project_title}

Your request to join "${project_title}" on OpenPlans has been approved.  The project is accessible at the following address: ${project_url}
""")

request_denied = _(u"""Subject: OpenPlans - Your request to join ${project_title}

Your request to join "${project_title}" on OpenPlans has been denied.
""")

invitation_retracted = _(u"""Subject: OpenPlans - Invitation to join  ${project_title}

The invitation extended to you to join "${project_title}" on OpenPlans has been revoked.
""")

membership_deactivated = _(u"""Subject: OpenPlans - Membership deactivated for ${project_title}

You are no longer a member of "${project_title}" on OpenPlans.
""")

membership_requested = _(u"""Subject: OpenPlans - Request to join ${project_title}

${member_id}, ${member_fullname}, would like to get involved with "${project_title}".

To approve or deny this request please visit the project's team management screen: ${team_manage_url}
""")

mship_request_message = _(u"""

${member_id}, ${member_fullname}, included the following message:

"${member_message}"
""")

invite_email = _(u"""Subject: OpenPlans - Invitation to join ${project_title}

You have been invited to join "${project_title}" on OpenPlans.

If you would like to get involved, set up an OpenPlans account: ${join_url}

OpenPlans is a free toolset for social change. With OpenPlans, you can build collaborative pages for organizing projects. You can also blog, set up mailing lists, store and share files, and keep track of tasks.

We hope you'll take OpenPlans for a spin.

Cheers,
The OpenPlans Team
www.openplans.org
""")
