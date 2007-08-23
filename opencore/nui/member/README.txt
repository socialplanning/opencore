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
    
    >>> m1_folder.restrictedTraverse("account")
    <Products.Five.metaclass.MemberAccountView object at ...>

Test member portrait traversal
==============================

    >>> member = portal.portal_memberdata.m1
    >>> member.setPortrait(portrait)
    >>> member.restrictedTraverse("portrait_thumb")
    <Image at /plone/portal_memberdata/m1/portrait_thumb>

    >>> member.restrictedTraverse("portrait_icon")
    <Image at /plone/portal_memberdata/m1/portrait_icon>

    >>> member.restrictedTraverse("portrait_thumb").width
    63

    >>> member.restrictedTraverse("portrait_thumb").height
    80

Exercise the Member Account Class
=====================================

    Instantiate the view
    >>> from opencore.nui.member import MemberAccountView
    >>> request = self.app.REQUEST
    >>> request.form = {}

    # this should not be the member ... but the member folder
    # member works though, because the interface we need matches
    # (getId)

    >>> view = MemberAccountView(member, request)
    >>> view = view.__of__(member)
    >>> view
    <opencore.nui.member.view.MemberAccountView object at ...>

    Check projects for user m1
    >>> project_dicts = view.projects_for_user

    Check the projects and active states
    >>> [d['proj_id'] for d in project_dicts]
    ['p2', 'p3', 'p1']
    >>> [d['title'] for d in project_dicts]
    ['Project Two', 'Project Three', 'Project One']
    >>> [d['listed'] for d in project_dicts]
    [True, True, True]

    Now, let's have a member leave a project::

    But first, if we're not logged in as the member,
    we should get a portal status message back and a False return
    >>> view.leave_project('p2')
    False
    >>> view.portal_status_message
    [u'You cannot leave this project.']

    We have to login as m1 to get the modify portal content permission,
    giving us access to the workflow transition
    >>> self.logout()
    >>> self.login('m1')

    Now we should be able to leave the project just fine
    >>> view.leave_project('p2')
    True

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
    [True, True]

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
    >>> view.nupdates()
    1

    Let's try leaving a project pending from a member request
    >>> view.leave_project('p2')
    True

    >>> self.clearMemoCache()
    >>> project_dicts = view.projects_for_user
    >>> [d['proj_id'] for d in project_dicts]
    ['p3', 'p1']

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

    Now we can trigger them, we get the json response
    >>> sorted(view.accept_handler(['p4']).keys())
    ['num_updates', 'p4_invitation', 'projinfos_for_user']

    And thus, we should no longer be invited
    >>> self.clearMemoCache()
    >>> view.invitations()
    []

    But a part of the project
    >>> sorted([d['proj_id'] for d in view.projects_for_user])
    ['p1', 'p3', 'p4']

And now if we were to receive an info message::

    Let's stick some phony messages in there first
    >>> tm = getUtility(ITransientMessage, context=self.portal)
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
    ['p1', 'p3', 'p4']

    What happens if we try to perform an action on something that doesn't
    exist? Right now we get a portal status message
    >>> view.deny_handler(['p2'])
    {}
    >>> view.portal_status_message
    []

Check that changing passwords works

    We'll need to modify some request variables
    >>> request = view.request.form = {}

    Let's check without setting any fields
    >>> view.change_password()
    >>> view.portal_status_message
    [u'Please check the old password you entered.']

    Now we set the old password to what it should be,
    so that we get different portal status messages
    >>> request['passwd_curr'] = 'testy'
    >>> view.change_password()
    >>> view.portal_status_message
    [u'You must enter a password.']

    Set a new password
    >>> request['password'] = 'foo'
    >>> view.change_password()
    >>> view.portal_status_message
    [u'You must enter a password.']

    Set all the required fields
    and the passwords don't match
    >>> request['password2'] = 'bar'
    >>> view.change_password()
    >>> view.portal_status_message
    [u'Please make sure that both password fields are the same.']

    Now we set the same passwordz, only not enough characters
    >>> request['password'] = 'abc'
    >>> request['password2'] = 'abc'
    >>> view.change_password()
    >>> view.portal_status_message
    [u'Passwords must contain at least 5 characters.']

    And if we try to change to the same password?
    We act as if it was a successful change
    >>> request['passwd_curr'] = 'testy'
    >>> request['password'] = 'testy'
    >>> request['password2'] = 'testy'
    >>> view.change_password()
    >>> view.portal_status_message
    [u'Your password has been changed.']

    And finally, the last hoorah!
    >>> request['password'] = 'hoorah'
    >>> request['password2'] = 'hoorah'
    >>> view.change_password()
    >>> view.portal_status_message
    [u'Your password has been changed.']

Members can also change their email address with this view
It's talented, isn't it?

    Reset the request, so there's no funny business
    >>> view.request.form = request = {}

    With no email set, we should get an error portal status message
    >>> view.change_email()
    >>> view.portal_status_message
    [u'Please enter your new email address.']

    Upon setting an invalid email, we get an appropriate message
    >>> request['email'] = 'foobarbazquux'
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
    >>> request['hide_email'] = '1'
    >>> request['email'] = 'notreal1@example.com'
    >>> view.change_email()
    >>> view.portal_status_message
    []
    >>> mem.getEmail()
    'notreal1@example.com'

    And if we use an email address that's already taken
    >>> request['email'] = 'notreal2@example.com'
    >>> view.change_email()
    >>> view.portal_status_message
    [u'That email address is already in use.  Please choose another.']

    # and check if you try to set it to the same email address
    # should have different messages for both

    And now actually change the email address
    >>> request['email'] = 'foobarbazquux@example.com'
    >>> view.change_email()
    >>> view.portal_status_message
    [u'Your email address has been changed.']

    And let's check the member's email, which should be changed to the new one
    >>> mem.getEmail()
    'foobarbazquux@example.com'

    And if we change the anonymous setting, it should change the
    visibility on the member object
    >>> del request['hide_email']
    >>> view.change_email()
    >>> view.portal_status_message
    [u'Default email is not anonymous']
    
    Now if we change both at the same time,
    we should get 2 portal status messages
    >>> request['hide_email'] = '1'
    >>> request['email'] = 'zul@example.com'
    >>> view.change_email()
    >>> psms = view.portal_status_message
    >>> len(psms)
    2
    >>> psms[0]
    u'Default email is anonymous'
    >>> psms[1]
    u'Your email address has been changed.'

    And the member object should have changed
    >>> mem.getEmail()
    'zul@example.com'
    >>> mem.getUseAnonByDefault()
    True

Verify invitations view works appropriately

    Instantiate the view
    >>> from opencore.nui.member.view import InvitationView
    >>> view = InvitationView(member, view.request)
    >>> view.request.form = request = {}
    
    And the utility where we manage email invites
    >>> email_inviter = getUtility(IEmailInvites, context=self.portal)
    >>> email_inviter
    <EmailInvites at /plone/utilities/>

    Shouldn't have any messages currently
    >>> email = mem.getEmail()
    >>> list(email_inviter.getInvitesByEmailAddress(email))
    []
    >>> dict(email_inviter.getInvitesByEmailAddress(email))
    {}

    Let's confirm that the view agrees with us
    >>> from opencore.nui.member.view import ProfileEditView
    >>> profileeditview = ProfileEditView(member, view.request)
    >>> profileeditview.has_invitations()
    False

    Let's remove the member object that's currently there
    >>> proj_team = pt.p2
    >>> proj_team.manage_delObjects(['m1'])

    And now let's add an invitation
    >>> email_inviter.addInvitation(email, 'p2')

    Now the login view should say we have invitations
    >>> profileeditview.has_invitations()
    True

    And ask the view for the invitation structures
    >>> projinfos = view.projinfos()
    >>> len(projinfos)
    1
    >>> pprint(dict(projinfos[0]))
    {'proj_id': 'p2',
     'since': 'today',
     'title': 'Project Two',
     'url': 'http://nohost/plone/projects/p2'}

    After joining the project, the invitation should be removed
    >>> view.handle_join(['p2'])
    {'proj_p2': {'action': 'delete'}}

    And the membership object should be there, and it should be active
    >>> mship = proj_team.m1
    >>> wft.getInfoFor(mship, 'review_state')
    'public'

    And finally, the invitation should no longer exist
    >>> profileeditview.has_invitations()
    False
    >>> bt = email_inviter.getInvitesByEmailAddress(mem.getEmail())
    >>> list(bt)
    []



    Now let's call the view simulating the request:
    XXX member areas need to be created first though for m1
    or we can't traverse to view (or get people folder)
