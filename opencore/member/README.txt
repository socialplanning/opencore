A member should implement IOpenMember::
    >>> mem = self.portal.portal_memberdata.m1
    >>> mem
    <OpenMember at /plone/portal_memberdata/m1>
    >>> from opencore.member.interfaces import IOpenMember
    >>> IOpenMember.providedBy(mem)
    True

---------------
member workflow 
---------------

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
    (if we had one but i don't feel like setting this up now)

But this method doesn't do any error checking of its own, so if we
try to confirm an account that's already confirmed we'll get an
exception from portal_workflow::
    >>> IHandleMemberWorkflow(mem).confirm()
    Traceback (most recent call last):
    ...
    WorkflowException: No workflow provides the "register_public" action.

---------------
member creation
---------------

We also have a convenient way to handle the steps of initial member
creation::

    >>> from opencore.member.interfaces import ICreateMembers
    >>> ICreateMembers(self.portal)
    <opencore.member.factory.MemberFactory object at ...>
    >>> factory = ICreateMembers(self.portal)

There's secretly a validation member somewhere on the portal because
ploneish validation is rather silly and requires real content upon
which to validate::
    >>> factory._validation_member
    <OpenMember at /plone/portal_memberdata/validation_member>
    
There's also a way to fake a request, or at least the bits that the
validation methods on content care about::
    >>> from opencore.member.factory import _FakeRequest
    >>> req = _FakeRequest(dict(x=1,b=2))
    >>> req
    <opencore.member.factory._FakeRequest object at ...>
    >>> sorted(req.form.keys())
    ['b', 'x']
    >>> req['x']
    1
    >>> req.get('b')
    2
    
These are used to validate fields but we don't know that because of
the lovely validate method on the adapter::
    >>> factory.validate(dict(id='foo',
    ...                       email='greeble@example.com',
    ...                       password='testy',
    ...                       confirm_password='testy'))
    {}
    >>> errors = factory.validate(dict(id='m1', email='greexampledotcom'))
    >>> sorted(errors.keys())
    ['email', 'id', 'password']

future We can also create a member without remembering how to go through a
future complicated dance involving portal_factory and validation::
future     >>> factory.create(baz)

