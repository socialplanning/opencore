=========================
 opencore.member.browser
=========================

Test registration of member related views::

    >>> m1_folder = self.portal.people.test_user_1_
    >>> alsoProvides(m1_folder, IMemberFolder)
    >>> m1_folder.restrictedTraverse("profile-edit")
    <Products.Five.metaclass.ProfileEditView...>

    >>> m1_folder.restrictedTraverse("profile")
    <...SimpleViewClass ...profile.pt object...>
    
    >>> m1_folder.restrictedTraverse("account")
    <Products.Five.metaclass.MemberAccountView object at ...>

Test member portrait traversal
==============================

    >>> member = portal.portal_memberdata.m1
    >>> member.setPortrait(portrait)

Check we can traverse to new portrait in various sizes::

    >>> member.restrictedTraverse("portrait_thumb")
    <Image at /plone/portal_memberdata/m1/portrait_thumb>

    >>> member.restrictedTraverse("portrait_icon")
    <Image at /plone/portal_memberdata/m1/portrait_icon>

Check scaling on thumbnail::

    >>> member.restrictedTraverse("portrait_thumb").width
    63

    >>> member.restrictedTraverse("portrait_thumb").height
    80

Exercise the Member Account Class
=================================

    Instantiate the view::

    >>> from opencore.member.browser.view import MemberAccountView
    >>> request = self.app.REQUEST
    >>> request.form = {}

    # this should not be the member ... but the member folder
    # member works though, because the interface we need matches
    # (getId)

    >>> view = MemberAccountView(member, request)
    >>> view = view.__of__(member)
    >>> view
    <...MemberAccountView object at ...>

    Login as the m1 user::

    >>> self.login('m1')

Create a project with an international unicode title::
    >>> from opencore.project.browser.view import ProjectAddView
    >>> proj_add_view = ProjectAddView(self.portal.projects,
    ...                                self.portal.REQUEST)
    >>> request.form['projid'] = 'i18n'

This is some japanese that I found::
    >>> request.form['title'] = u'\u65e5\u8a9e'
    >>> request.form['workflow_policy'] = 'medium_policy'
    >>> request.form['__initialize_project__'] = True
    >>> html = proj_add_view.handle_request()
    >>> japanese_project = self.portal.projects.i18n
    >>> japanese_project
    <OpenProject at /plone/projects/i18n>
    >>> delattr(proj_add_view, '_redirected')

Create a project starting with a capital letter to test case
insensitive sort::
    >>> proj_add_view = ProjectAddView(self.portal.projects,
    ...                                self.portal.REQUEST)
    >>> request.form['projid'] = 'apples'
    >>> request.form['title'] = 'apples are good'
    >>> request.form['workflow_policy'] = 'medium_policy'
    >>> request.form['__initialize_project__'] = True
    >>> html = proj_add_view.handle_request()
    >>> apple_project = self.portal.projects.apples
    >>> apple_project
    <OpenProject at /plone/projects/apples>
    >>> delattr(proj_add_view, '_redirected')

Check projects for user m1::
    >>> project_dicts = view.projects_for_user

Check the projects and active states (these are sorted on project title)::
    >>> sorted([d['proj_id'] for d in project_dicts])
    ['apples', 'i18n', 'p1', 'p2', 'p3']

XXXX Notice that the project title here isn't properly unicode for some reason. I feel like this might be a problem::
    >>> sorted([d['title'] for d in project_dicts])
    ['Project One', 'Project Three', 'Project Two', 'apples are good', '\xe6\x97\xa5\xe8\xaa\x9e']
    >>> [d['listed'] for d in project_dicts]
    [True, True, True, True, True]

    Now, let's have a member leave a project::

    But first, if we're not logged in as the member,
    we should get a portal status message back and a False return
    >>> self.logout()
    >>> self.login('test_user_1_')
    >>> view.leave_project('p2')
    False
    >>> view.portal_status_message
    [u'You cannot leave this project.']

    We have to login as m1 to get the modify portal content permission,
    giving us access to the workflow transition
    >>> self.logout()
    >>> self.login('m1')

    Now we should be able to leave the project just fine
    The proper event should get fired as well
    >>> self.clear_events()
    >>> view.leave_project('p2')
    True

    A role change event gets fired in addition to a left project event
    >>> len(self.events)
    2
    >>> obj, event = self.events[0]
    >>> from opencore.interfaces.event import IChangedTeamRolesEvent
    >>> IChangedTeamRolesEvent.providedBy(event)
    True
    >>> obj, event = self.events[1]
    >>> from opencore.interfaces.event import ILeftProjectEvent
    >>> ILeftProjectEvent.providedBy(event)
    True

    And finally, m1 should no longer have active membership to project p2
    >>> self.clearMemoCache()
    >>> project_dicts = view.projects_for_user
    >>> sorted([d['proj_id'] for d in project_dicts])
    ['apples', 'i18n', 'p1', 'p3']

If we try to leave a project with an international title which has no
other members, we should not be able to leave, and the system should
not explode::
    >>> view.leave_project('i18n')
    False
    >>> view.portal_status_message
    [u'You are the only remaining administrator of "\u65e5\u8a9e"...]

    Now we'll try to set the listing as private:

    First though, let's verify that he is currently listed as public
    >>> [d['listed'] for d in project_dicts]
    [True, True, True, True]

    Now let's make him private for project 3
    >>> view.change_visibility('p3')
    True

    When we get the projects again, we should not be listed for p3
    >>> self.clearMemoCache()
    >>> project_dicts = view.projects_for_user
    >>> sorted([(d['proj_id'], d['listed']) for d in project_dicts])
    [('apples', True), ('i18n', True), ('p1', True), ('p3', False)]

    And he should still be able to leave a project when private
    >>> view._can_leave('p3')
    True

    Now let's set it back to visible
    >>> view.change_visibility('p3')
    True

    Now he should be listed again
    >>> self.clearMemoCache()
    >>> project_dicts = view.projects_for_user
    >>> [d['listed'] for d in project_dicts]
    [True, True, True, True]

    Check invitations for m1
    >>> view.invitations()
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
    >>> project_dicts = view.invitations()
    >>> len(project_dicts)
    1
    >>> proj = project_dicts[0]
    >>> proj['proj_id']
    'p4'

    Member is pending
    >>> proj['is_pending']
    True

    Pending members will have a false listing
    But it really doesn't matter because they don't get a listed column
    >>> proj['listed']
    False

    And one should still be pending, which project admins approve
    >>> self.clearMemoCache()
    >>> project_dicts = view.member_requests
    >>> [p['proj_id'] for p in project_dicts]
    ['p2']

    When we get all projects, the member request should be in there
    >>> self.clearMemoCache()
    >>> project_dicts = view.projects_for_user
    >>> sorted([d['proj_id'] for d in project_dicts])
    ['apples', 'i18n', 'p1', 'p2', 'p3']

    Check the info messages on the member:
    >>> list(view.infomsgs)
    []

    And verify that taking the length of updates works
    >>> view.nupdates()
    1

    Let's try leaving a project pending from a member request
    >>> view.leave_project('p2')
    True

    >>> self.clearMemoCache()
    >>> project_dicts = view.projects_for_user
    >>> sorted([d['proj_id'] for d in project_dicts])
    ['apples', 'i18n', 'p1', 'p3']

    And when we try to leave a pending mship that's an invitation
    (should never happen, but with users messing with request) We
    should not have left anyting

    >>> self.clearMemoCache()
    >>> view.leave_project('p4')
    False

If we try to leave a project as the only admin, it should not allow
it, and return an appropriate portal status message

    First though, let's get rid of the portal_owner
    >>> proj_team = pt.p3
    >>> proj_team.removeMember('portal_owner')

    Now we can try to leave the project
    >>> view.leave_project('p3')
    False
    >>> view.portal_status_message
    [u'You are the only remaining administrator ... leave this project without appointing another.']

    Even if we are in the private state
    >>> view.change_visibility('p3')
    True
    >>> view.leave_project('p3')
    False
    >>> view.portal_status_message
    [u'You are the only remaining administrator ... leave this project without appointing another.']

    >>> project_dicts = view.invitations()
    >>> [d['proj_id'] for d in project_dicts]
    ['p4']

    Here are the actions that can be performed on each invitation
    request

    >>> view.invitation_actions
    ['Accept', 'Deny']

Let's accept our gracious invitation

    First though, we have to set async mode on the request to test
    octopolite methods

    >>> view.request.form = dict(mode='async')

    And we should verify that the proper events get sent
    >>> self.clear_events()

    Now we can trigger them, we get the json response
    >>> sorted(view.accept_handler(['p4']).keys())
    ['num_updates', 'p4_invitation', 'projinfos_for_user']

    Now we can check that we got the event
    >>> len(self.events)
    1
    >>> obj, event = self.events[0]
    >>> from opencore.interfaces.event import IJoinedProjectEvent
    >>> IJoinedProjectEvent.providedBy(event)
    True

    And thus, we should no longer be invited
    >>> self.clearMemoCache()
    >>> view.invitations()
    []

    But a part of the project
    >>> sorted([d['proj_id'] for d in view.projects_for_user])
    ['apples', 'i18n', 'p1', 'p3', 'p4']

And now if we were to receive an info message::

    Let's stick some phony messages in there first
    >>> tm = ITransientMessage(self.portal)
    >>> tm.store('m1', view.msg_category, 'All your base are belong to us')
    >>> tm.store('m1', view.msg_category, 'You were just acceped to Move Zig')

    And now we should be able to view those messages
    >>> list(view.infomsgs)
    [(0, 'All your base are belong to us'), (1, 'You were just acceped to Move Zig')]

    Let's go ahead and kill the first one, the message is not so nice
    >>> sorted(view.close_msg_handler('0').keys())
    ['0_close', 'num_updates']

    Poof, he's gone
    >>> self.clearMemoCache()
    >>> list(view.infomsgs)
    [(1, 'You were just acceped to Move Zig')]

    And if we try to axe something that isn't there ...
    We get zilch back
    >>> view.close_msg_handler(['42'])
    {}

Let's also reject an invitation extended to us::

    First thing we have to do, is simulate an admin inviting us
    Turns out that we still have a reference to a project we can get invited
    to. Let's re-use that, and invite member one as an admin
    >>> proj_team = team_request
    >>> self.logout()
    >>> self.loginAsPortalOwner()
    >>> proj_team.removeMember('m1')
    >>> proj_team.addMember('m1')
    <OpenMembership at /plone/portal_teams/p2/m1>
    >>> self.logout()
    >>> self.login('m1')

    So we're invited
    >>> self.clearMemoCache()
    >>> [d['proj_id'] for d in view.invitations()]
    ['p2']

    Now we shove it back in the admin's face
    >>> sorted(view.deny_handler(['p2']).keys())
    ['num_updates', 'p2_invitation']

    And we're not a part of that project, and no longer invited
    >>> self.clearMemoCache()
    >>> view.invitations()
    []
    >>> sorted([d['proj_id'] for d in view.projects_for_user])
    ['apples', 'i18n', 'p1', 'p3', 'p4']

    What happens if we try to perform an action on something that doesn't
    exist? Right now we get a portal status message
    >>> view.deny_handler(['p2'])
    {}
    >>> view.portal_status_message
    []

Check that changing passwords works

    Let's check without setting any fields
    >>> request.form = {}
    >>> view.change_password()
    >>> view.portal_status_message
    [u'Please check the old password you entered.']

    Now we set the old password to what it should be,
    so that we get different portal status messages
    >>> request.form['passwd_curr'] = 'testy'
    >>> view.change_password()
    >>> view.portal_status_message
    [u'You must enter a password.']

    Set a new password
    >>> request.form['password'] = 'foo'
    >>> view.change_password()
    >>> view.portal_status_message
    [u'You must enter a password.']

    Set all the required fields
    and the passwords don't match
    >>> request.form['password2'] = 'bar'
    >>> view.change_password()
    >>> view.portal_status_message
    [u'Please make sure that both password fields are the same.']

    Now we set the same passwordz, only not enough characters
    >>> request.form['password'] = 'abc'
    >>> request.form['password2'] = 'abc'
    >>> view.change_password()
    >>> view.portal_status_message
    [u'Passwords must contain at least 5 characters.']

    Try for the password "password"
    >>> request.form['password'] = 'password'
    >>> request.form['password2'] = 'password'
    >>> view.change_password()
    >>> view.portal_status_message
    [u'"password" is not a valid password.']

    And if we try to change to the same password?
    We act as if it was a successful change
    >>> request.form['passwd_curr'] = 'testy'
    >>> request.form['password'] = 'testy'
    >>> request.form['password2'] = 'testy'
    >>> view.change_password()
    >>> view.portal_status_message
    [u'Your password has been changed.']

    And finally, the last hoorah!
    >>> request.form['password'] = 'hoorah'
    >>> request.form['password2'] = 'hoorah'
    >>> view.change_password()
    >>> view.portal_status_message
    [u'Your password has been changed.']

Members can also change their email address with this view
It's talented, isn't it?

    Reset the request, so there's no funny business
    >>> view.request.form = {}

    With no email set, we should get an error portal status message
    >>> view.change_email()
    >>> view.portal_status_message
    [u'Please enter your new email address.']

    Upon setting an invalid email, we get an appropriate message
    >>> request.form['email'] = 'foobarbazquux'
    >>> view.change_email()
    >>> view.portal_status_message
    [u'That email address is invalid.']

    If we set a legitimate one, then all should be well
    First though, let's check to make we are set with the old one
    >>> mem = self.portal.portal_memberdata.m1
    >>> mem.getEmail()
    'notreal1@example.com'

    If we try to change to the same email address, nothing happens
    And we don't get a portal status message
    But we have to set the anonymous email setting first
    >>> mem.getUseAnonByDefault()
    True
    >>> request.form['email'] = 'notreal1@example.com'
    >>> view.change_email()
    >>> view.portal_status_message
    []
    >>> mem.getEmail()
    'notreal1@example.com'

    And if we use an email address that's already taken
    >>> request.form['email'] = 'notreal2@example.com'
    >>> view.change_email()
    >>> view.portal_status_message
    [u'That email address is already in use.  Please choose another.']

    # and check if you try to set it to the same email address
    # should have different messages for both

    And now actually change the email address
    and verify that the proper event was sent
    >>> self.clear_events()
    >>> request.form['email'] = 'foobarbazquux@example.com'
    >>> view.change_email()
    Called httplib2.Http.request(
        'http://nohost:wordpress/openplans-change-email.php',
        'POST',
        body='...',
        headers={...})

    >>> len(self.events)
    1
    >>> from opencore.interfaces.event import IMemberEmailChangedEvent
    >>> obj, event = self.events[0]
    >>> IMemberEmailChangedEvent.providedBy(event)
    True
    >>> view.portal_status_message
    [u'Your email address has been changed.']

    And let's check the member's email, which should be changed to the new one
    >>> mem.getEmail()
    'foobarbazquux@example.com'

    The membrane tool should also have an updated entry for the email address
    >>> brains = list(self.portal.membrane_tool(getId='m1'))
    >>> len(brains)
    1
    >>> brains[0].getEmail
    'foobarbazquux@example.com'

If we leave a project where we are a ProjectAdmin, we should no longer
have the ProjectAdmin role::
    >>> japanese_team = self.portal.portal_teams.i18n
    >>> japanese_team.getHighestTeamRoleForMember('m1')
    'ProjectAdmin'

    >>> request = self.app.REQUEST
    >>> view = MemberAccountView(member, request)
    >>> view = view.__of__(member)
    >>> view
    <...MemberAccountView object at ...>

    >>> view._apply_transition_to('i18n', 'deactivate')
    True
    >>> japanese_team.getHighestTeamRoleForMember('m1')
    'ProjectMember'

    Now let's call the view simulating the request:
    XXX member areas need to be created first though for m1
    or we can't traverse to view (or get people folder)
