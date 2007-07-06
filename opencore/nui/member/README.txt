=====================
 opencore.nui.member
=====================

Test registration of member related views::

    >>> m1_folder = self.portal.people.test_user_1_
    >>> alsoProvides(m1_folder, IMemberFolder)
    >>> m1_folder.restrictedTraverse("profile-edit")
    <...SimpleViewClass ...profile-edit.pt...>

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

    When we get the projects again, we should not be listed for p3
    >>> self.clearMemoCache()
    >>> project_dicts = view.projects_for_user
    >>> [d['listed'] for d in project_dicts]
    [False, True]

    Now let's set it back to visible
    >>> view.change_visibility('p3')

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

    Now we should one invitation for m1
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

    Now let's call the view simulating the request:
    XXX member areas need to be created first though for m1
    or we can't traverse to view (or get people folder)
