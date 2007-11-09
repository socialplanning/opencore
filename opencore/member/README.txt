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
