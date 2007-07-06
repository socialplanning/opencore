=====================
 opencore.nui.member
=====================

Test registration of member related views::

    >>> m1_folder = self.portal.people.test_user_1_
    >>> alsoProvides(m1_folder, IMemberFolder)
    >>> m1_folder.restrictedTraverse("profile-edit")
    <Products.Five.metaclass.ProfileEditView...>

    >>> m1_folder.restrictedTraverse("profile")
    <...SimpleViewClass ...profile.pt object...>
    
    >>> m1_folder.restrictedTraverse("preferences")
    <Products.Five.metaclass.MemberPreferences object at ...>


Exercise the Member Preferences Class
=====================================

    Instantiate the view
    >>> from opencore.nui.member import MemberPreferences
    >>> request = self.app.REQUEST
    >>> request.form = {}

    # this should not be the member ... but the member folder
    # member works though, because the interface we need matches
    # (getId)
    >>> member_folder = portal.portal_memberdata.m1

    >>> view = MemberPreferences(member_folder, request)
    >>> view
    <opencore.nui.member.view.MemberPreferences object at ...>

    Check projects for user m1
    >>> project_dicts = view.projects_for_user

    Check the projects and active states
    >>> [d['proj_id'] for d in project_dicts]
    ['p2', 'p3', 'p1']
    >>> [d['title'] for d in project_dicts]
    ['Proj2', 'Proj3', 'Proj1']
    >>> [d['listed'] for d in project_dicts]
    [True, True, True]

    Now, let's have a member leave a project::

    But first, if we're not logged in as the member,
    we should get a workflow exception when trying to leave the project
    >>> view.leave_project('p2')
    Traceback (most recent call last):
    ...
    WorkflowException: No workflow provides the "deactivate" action.

    We have to login as m1 to get the modify portal content permission,
    giving us access to the workflow transition
    >>> self.logout()
    >>> self.login('m1')

    Now we should be able to leave the project just fine
    >>> view.leave_project('p2')

    And finally, m1 should no longer have active membership to project p2
    >>> self.clearMemoCache()
    >>> project_dicts = view.projects_for_user
    >>> [d['proj_id'] for d in project_dicts]
    ['p3', 'p1']

    Now we'll try to set the listing as private:

    First though, let's verify that he is currently listed as public
    >>> [d['listed'] for d in project_dicts]
    [True, True]

    Now let's make him private for project 3
    >>> view.change_visibility('p3')
    True

    When we get the projects again, we should not be listed for p3
    >>> self.clearMemoCache()
    >>> project_dicts = view.projects_for_user
    >>> [d['listed'] for d in project_dicts]
    [False, True]

    Now let's set it back to visible
    >>> view.change_visibility('p3')
    True

    Now he should be listed again
    >>> self.clearMemoCache()
    >>> project_dicts = view.projects_for_user
    >>> [d['listed'] for d in project_dicts]
    [True, True]

    Check invitations for m1
    >>> view.invitations
    []

    Let's simulate a project admin inviting a user
    And also a user requesting membership to a project
    >>> pt = getToolByName(portal, 'portal_teams')
    >>> team_request = pt._getOb('p2')
    >>> team_invite = pt._getOb('p4')

    First simulate a user requesting membership by pushing him through the
    workflow transition
    >>> m1_p2_mship = team_request._getOb('m1')
    >>> wft = getToolByName(self.portal, 'portal_workflow')
    >>> wft.doActionFor(m1_p2_mship, 'rerequest')

    Now, simulate a project admin inviting a user
    >>> self.logout()
    >>> self.loginAsPortalOwner()
    >>> team_invite.addMember('m1')
    <OpenMembership at /plone/portal_teams/p4/m1>
    >>> self.logout()
    >>> self.login('m1')

    Now we should have one invitation for m1
    These are what the member can act on
    >>> self.clearMemoCache()
    >>> project_dicts = view.invitations
    >>> len(project_dicts)
    1
    >>> proj = project_dicts[0]
    >>> proj['proj_id']
    'p4'

    Pending members should be listed as public
    >>> proj['listed']
    True

    And one should still be pending, which project admins approve
    >>> self.clearMemoCache()
    >>> project_dicts = view.member_requests
    >>> [p['proj_id'] for p in project_dicts]
    ['p2']

    When we get all projects, the member request should be in there
    >>> self.clearMemoCache()
    >>> project_dicts = view.projects_for_user
    >>> [d['proj_id'] for d in project_dicts]
    ['p2', 'p3', 'p1']

    Check the info messages on the member:
    >>> list(view.infomsgs)
    []

    And verify that taking the length of updates works
    >>> view.n_updates
    1

    Let's try leaving a project pending from a member request
    >>> view.leave_project('p2')
    >>> self.clearMemoCache()
    >>> project_dicts = view.projects_for_user
    >>> [d['proj_id'] for d in project_dicts]
    ['p3', 'p1']

    And when we try to leave a pending mship that's an invitation
    (should never happen, but with users messing with post)
    We should not have left anyting
    >>> self.clearMemoCache()
    >>> view.leave_project('p4')
    >>> project_dicts = view.invitations
    >>> [d['proj_id'] for d in project_dicts]
    ['p4']

    Here are the actions that can be performed on each invitation request
    >>> view.invitation_actions
    ['Accept', 'Deny', 'Ignore']

Let's accept our gracious invitation

    First though, we have to set async mode on the request to test octopolite
    methods
    >>> view.request.form = dict(mode='async')

    Now we can trigger them, we get the json response
    >>> view.accept_handler(['p4'])
    {'p4_invitation': {'action': 'delete'}}

    And thus, we should no longer be invited
    >>> self.clearMemoCache()
    >>> view.invitations
    []

    But a part of the project
    >>> sorted([d['proj_id'] for d in view.projects_for_user])
    ['p1', 'p3', 'p4']

And now if we were to receive an info message

    Let's stick some phony messages in there first
    >>> tm = getUtility(ITransientMessage)
    >>> tm.store('m1', view.msg_category, 'All your base are belong to us')
    >>> tm.store('m1', view.msg_category, 'You were just acceped to Move Zig')

    And now we should be able to view those messages
    >>> list(view.infomsgs)
    [(0, 'All your base are belong to us'), (1, 'You were just acceped to Move Zig')]

    Let's go ahead and kill the first one, the message is not so nice
    >>> view.close_msg_handler('0')
    {'0_close': {'action': 'delete'}}

    Poof, he's gone
    >>> self.clearMemoCache()
    >>> list(view.infomsgs)
    [(1, 'You were just acceped to Move Zig')]

    And if we try to axe something that isn't there ...
    We get zilch back
    >>> view.close_msg_handler(['42'])
    {}

Let's also reject an invitation extended to us

    First thing we have to do, is simulate an admin inviting us
    Turns out that we still have a reference to a project we can get invited
    to. Let's re-use that, and invite member one as an admin
    >>> proj_team = team_request
    >>> self.logout()
    >>> self.loginAsPortalOwner()
    >>> proj_team._delOb('m1')
    >>> proj_team.addMember('m1')
    <OpenMembership at /plone/portal_teams/p2/m1>
    >>> self.logout()
    >>> self.login('m1')

    So we're invited
    >>> self.clearMemoCache()
    >>> [d['proj_id'] for d in view.invitations]
    ['p2']

    Now we shove it back in the admin's face
    >>> view.deny_handler(['p2'])
    {'p2_invitation': {'action': 'delete'}}

    And we're not a part of that project, and no longer invited
    >>> self.clearMemoCache()
    >>> view.invitations
    []
    >>> sorted([d['proj_id'] for d in view.projects_for_user])
    ['p1', 'p3', 'p4']

    What happens if we try to perform an action on something that doesn't
    exist? Right now we get a workflow exception ... maybe we should be more
    graceful?
    >>> view.deny_handler(['p2'])
    Traceback (most recent call last):
    ...
    WorkflowException: No workflow provides the "reject_by_owner" action.

    Now let's call the view simulating the request:
    XXX member areas need to be created first though for m1
    or we can't traverse to view (or get people folder)
