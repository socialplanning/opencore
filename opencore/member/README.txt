A member should implement IOpenMember::
    >>> mem = self.portal.portal_memberdata.m1
    >>> mem
    <OpenMember at /plone/portal_memberdata/m1>
    >>> from opencore.member.interfaces import IOpenMember
    >>> IOpenMember.providedBy(mem)
    True

We have a convenient way to talk about member workflow via the
IHandleMemberWorkflow adapter::
    >>> from opencore.member.interfaces import IHandleMemberWorkflow
    >>> IHandleMemberWorkflow(mem)
    <opencore.member.workflow.MemberWorkflowHandler object at ...>

It lets us determine if a user's account is unconfirmed::
    >>> IHandleMemberWorkflow(mem).is_unconfirmed()
    False

We can also see the member's state directly, but this isn't part of
the interface because the whole point of this is to abstract away from
portal_workflow and hardcoded strings::
    >>> IHandleMemberWorkflow(mem)._wfstate
    'public'

We can confirm a member account that is pending confirmation::

But this method doesn't do any error checking of its own, so if we
try to confirm an account that's already confirmed we'll get an
exception from portal_workflow::
    >>> IHandleMemberWorkflow(mem).confirm()
    Traceback (most recent call last):
    ...
    WorkflowException: No workflow provides the "register_public" action.
