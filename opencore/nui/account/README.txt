====================
 account management
====================

Forgot Password
===============

ensure you're logged out first::

    >>> self.logout()

the forgotten password view::

    >>> view = portal.restrictedTraverse("@@forgot")
    >>> view
    <...SimpleViewClass ...forgot.pt...>

    >>> view.request.form['send'] =  True
    >>> view.userid

With '__ac_name' set, it should find and confirm a userid::

    >>> view.request.form['__ac_name'] = 'test_user_1_'
    >>> view.userid
    'test_user_1_'

This should be the case even if the user forgets correct capitalization::

    >>> view.request.form['__ac_name'] = 'Test_User_1_'
    >>> view.userid
    'test_user_1_'

The member needs to have a 'legitimate' email address::

    >>> member = portal.membrane_tool(getUserName='test_user_1_')[0].getObject()
    >>> member
    <OpenMember at /plone/portal_memberdata/test_user_1_>
    >>> member.setEmail('test_emailer_1_@example.com')

Running handle request does all this, and sends the email::

    >>> view.request.environ["REQUEST_METHOD"] = "POST"
    >>> view.handle_request()
    True

    >>> view.request.environ["REQUEST_METHOD"] = "GET"

Now we should be able to get a string for later matching::


    >>> randomstring = view.randomstring
    >>> randomstring
    '...'


Password Reset
==============

    >>> view = portal.restrictedTraverse("@@reset-password")
    >>> view
    <...SimpleViewClass ...reset-password.pt...>
    
If no key is set, we taunt you craxorz::

    >>> view.key
    Traceback (innermost last):
    ...
    Forbidden: Your password reset key is invalid. Please verify that it is identical to the email and try again.

But if a key is set, we can use it::

    >>> view.request.form['key']=randomstring
    >>> view.key == randomstring
    True

To do the reset, we'll need to submit the form::

    >>> view.request.environ["REQUEST_METHOD"] = "POST"
    >>> view.request.form["set"]=True
    >>> view.request.form["password"]='word'
    >>> view.request.form["password2"]='word'
    >>> view.request.form["userid"]='test_user_1_'
    >>> view.handle_reset()
    False

Why is this?

    >>> view.portal_status_message[-1]
    u'Passwords must contain at least 5 characters.'

Ensure that validate_password_form has the same functionality:

    >>> view.validate_password_form('word', 'word', 'test_user_1_')
    False
    >>> view.portal_status_message
    [u'Passwords must contain at least 5 characters.']

Now try non-matching passwords:

    >>> view.validate_password_form('wordy', 'werdy', 'test_user_1_')
    False
    >>> view.portal_status_message
    [u'Please make sure that both password fields are the same.']

Test doing the reset:

First, ensure there is no portal status message:
    >>> view.portal_status_message
    []

Next, ensure that we're using a valid password:
    >>> view.validate_password_form('wordy', 'wordy', 'test_user_1_')
    <OpenMember at ...>

This should work even with wrong capitalization and leading space:
    >>> view.validate_password_form('wordy', 'wordy', ' tESt_uSEr_1_')
    <OpenMember at ...>

Finally, handle the reset:

    >>> view.request.form["password"] = 'wordy'
    >>> view.request.form["password2"] = 'wordy'
    >>> view.handle_reset()
    True
    >>> expected = '/'.join((view.siteURL, 'people', 'test_user_1_', 'account'))
    >>> expected == view.request.response.getHeader('location')
    True

# XXX TODO:  login with the new password [maybe in the login section]

Get Account Confirmation Code
=============================

Get a user so that we can try to get a user's confirmation code for manual registration::

    >>> from Products.CMFCore.utils import getToolByName
    >>> mt = getToolByName(portal, "portal_memberdata")
    >>> user = mt.restrictedTraverse('m1')
    >>> user
    <OpenMember at ...>

    >>> user.setUserConfirmationCode()

The getUserConfirmationCode method should only be available to site managers::

    >>> m = user.restrictedTraverse("getUserConfirmationCode")
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'getUserConfirmationCode' in this context
    >>> self.login("m1")
    >>> m = user.restrictedTraverse("getUserConfirmationCode")    	
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'getUserConfirmationCode' in this context

When the method is accessible, it should return a string code for the user::

    >>> self.loginAsPortalOwner()
    >>> m = user.restrictedTraverse("getUserConfirmationCode")
    >>> m()
    '...'


Join
====

Test the join view by adding a member to the site::

    >>> view = portal.restrictedTraverse("@@join")

Log out and fill in the form::

    >>> self.logout()
    >>> view = portal.restrictedTraverse("@@join")
    >>> request = view.request
    >>> request.environ["REQUEST_METHOD"] = "GET"
    >>> form = dict(id='foobar',
    ...             email='foobar@example.com',
    ...             password= 'testy',
    ...             confirm_password='testy')
    >>> request.form.update(form)

The view has a validate() method which returns an error dict::

(Making the tests very ugly and commenting most out temporarily
 because return values from validate are hideous)
    >>> validate_map = view.validate()
    >>> len([i for i in validate_map.values() if i['html']])
    0
    >>> # request.form['confirm_password'] = 'mesty'
    >>> # request.form['email'] = 'fakeemail'
    >>> # sorted([i for i in view.validate().keys() if i.split('-')[1] in request.form])

#    ['confirm_password', 'email', 'password']

Test what happens when password is "password"

    >>> request.form = dict(id='foouser3',
    ...                     fullname='foo user',
    ...                     email='foo3@example.com',
    ...                     password='password',
    ...                     confirm_password='password',
    ...                     )
    >>> view.create_member()
    {'password': u'"password" is not a valid password.'}
    >>> view.errors
    {'password': u'"password" is not a valid password.'}


Test what happens when both passwords are blank

    >>> request.form = dict(id='foouser',
    ...                     fullname='foo user',
    ...                     email='foo@example.com',
    ...                     )
    >>> view.create_member()
    {'password': 'Please enter a password'}
    >>> view.errors
    {'password': 'Please enter a password'}
    >>> request.form.update(password='freddy',
    ...                     confirm_password='freddy',
    ...                     )
    >>> view.create_member()
    <OpenMember at /plone/portal_memberdata/foouser>
    >>> pprint(view.errors)
    {}
    >>> request.form = form

If you add 'task|validate' to the request before submitting
the form the validate() method will be triggered::

    >>> request.form['task|validate'] = 'Foo'
    >>> str(view())
    '...Join OpenPlans...'

The template was rerendered with the error messages; to get the error
dict directly, make the request asynchronous::

# XXX this should be fixed+uncommented or removed

#    >>> request.form['mode'] = 'async'
#    >>> sorted([i for i in view().keys() if i.split('-')[1] in request.form])
#    ['confirm_password', 'email', 'password']

Submit the form for real now; we need to add 'task|join' to the request
and delete the existing task::

    >>> del request.form['task|validate']
    >>> request.form['confirm_password'] = 'testy'
    >>> request.form['email'] = 'foobar@example.com'
    >>> request.form['task|join'] = 'Foo'
    >>> view = portal.restrictedTraverse("@@join")
    >>> validate_map = view.validate()
    >>> len([i for i in validate_map.values() if i['html']])
    0

Verify that the proper events gets sent out when a member gets created
    >>> events_fired = []
    >>> def event_fired(obj, event):
    ...     events_fired.append((obj, event))
    >>> from zope.component import provideHandler
    >>> from zope.app.event.interfaces import IObjectCreatedEvent
    >>> from Products.remember.interfaces import IReMember
    >>> provideHandler(event_fired,
    ...                adapts=[IReMember, IObjectCreatedEvent])
    
We need to make the request a POST::

    >>> request.environ["REQUEST_METHOD"] = "POST"
    >>> view.membertool.getMemberById('foobar')
    >>> unicode(view())
    u'...<!-- join form -->...'
    >>> view.membertool.getMemberById('foobar')
    <OpenMember at /plone/portal_memberdata/foobar...>
    >>> len(events_fired)
    1
    >>> obj, event = events_fired[0]
    >>> IObjectCreatedEvent.providedBy(event)
    True

Ensure that you can't join the site with another foobar::

    >>> view.portal_status_message  # clear PSMs
    [...]
    >>> view()
    u'...The login name you selected is already in use or is not valid. Please choose another...'
    
You also shouldn't be able to join with case-variants::

    >>> view.portal_status_message  # clear PSMs
    [...]
    >>> form = dict(id='FooBar',
    ...             email='foobartwo@example.com',
    ...             password='testy',
    ...             confirm_password='testy')
    >>> view.request.form.update(form)
    >>> view()
    u'...The login name you selected is already in use or is not valid. Please choose another...'

Email address are also unique::

    >>> form = dict(id='sevenofnine',
    ...             email='foobar@example.com',
    ...             password='testy',
    ...             confirm_password='testy')
    >>> view.request.form.update(form)
    >>> view()
    u'...That email address is already in use.  Please choose another...'

But we do allow appending to existing logins::
    >>> form = dict(id='foobar3',
    ...             email='foobarthree@example.com',
    ...             password='testy',
    ...             confirm_password='testy')
    >>> view.request.form.update(form)
    >>> 'Please choose another' not in view()
    True
    >>> view.membertool.getMemberById('foobar3')
    <OpenMember at /plone/portal_memberdata/foobar3...>

Confirm
=======

Test the account confirmation view:: (fill this in!)

Calling the view with no key in the request will fail and go to the login page::

    >>> view = portal.restrictedTraverse("@@confirm-account")
    >>> view()
    'http://nohost/plone/login'

Get the newly created member::

    >>> user = mt.restrictedTraverse('foobar')
    >>> user
    <OpenMember at /plone/portal_memberdata/foobar>

    >>> self.loginAsPortalOwner()
    >>> m = user.restrictedTraverse("getUserConfirmationCode")
    >>> key = m()
    >>> key
    '...'

Calling the view with the proper key will bring you to your account page::

    >>> view = portal.restrictedTraverse("@@confirm-account")
    >>> view.request.form.clear()
    >>> view.request.form['key'] = key
    >>> view()
    'http://nohost/plone/init-login'

Login
=====

Logout first

    >>> self.logout()
    >>> portal.portal_membership.getAuthenticatedMember()
    <SpecialUser 'Anonymous User'>

Get the login view

    >>> view = portal.restrictedTraverse('@@login')

Clear the portal status messages and form

    >>> view.portal_status_message
    [...]
    >>> view.request.form.clear()

Login [to be done]

    >>> view.request.form['__ac_name'] = 'foobar'
    >>> view.request.form['__ac_password'] = 'testy'
    >>> output = view()

[Output should really be the user's homepage.  but it isn't
due to the fact that PAS isn't called.  Deal with this later]


Javascript functionality for Vacuum
===================================

    >>> def normalize_whitespace(astring):
    ...      # just a little helper to avoid caring about indentation.
    ...      return '\n'.join([li.strip() for li in astring.split('\n')]).strip()


Logged out user:

    >>> self.logout()
    >>> jsview = portal.restrictedTraverse('@@user.js')
    >>> output = jsview()
    >>> print normalize_whitespace(output)
    OpenCore.login({
    loggedin: false
    });

Logged in user:

    >>> self.login()
    >>> output = jsview()
    >>> print normalize_whitespace(output)
    OpenCore.login({
    loggedin: true,
    id: 'test_user_1_',
    name: '',
    profileurl: 'http://nohost/plone/people/test_user_1_/profile',
    memberurl: 'http://nohost/plone/people/test_user_1_',
    website: '',
    email: 'test_emailer_1_@example.com'
    });


Verify initial login converts email invites to mship invites
============================================================

    Retrieve any member object for use in our test

    >>> mtool = getToolByName(portal, 'portal_membership')
    >>> tmtool = getToolByName(portal, 'portal_teams')
    >>> wftool = getToolByName(portal, 'portal_workflow')
    >>> mem_id = 'm1'
    >>> proj_id = 'p4'
    >>> mem = mtool.getMemberById(mem_id)
    >>> team = tmtool.getTeamById(proj_id) # <- m1 isn't a member
    >>> team._getOb(mem_id, None) is None
    True

    Artificially insert an email invite for the user (sacrificing a
    dead chicken or two in the process)

    >>> from zope.app.component.hooks import setSite, setHooks
    >>> setSite(portal)
    >>> setHooks()
    >>> from zope.component import getUtility
    >>> from opencore.nui.project.interfaces import IEmailInvites
    >>> email_invites = getUtility(IEmailInvites)
    >>> email_invites.addInvitation(mem.getEmail(), proj_id)

    Login as the member and trigger the 'init-login' view

    >>> self.login(mem_id)
    >>> view = portal.restrictedTraverse('init-login')
    >>> view()
    'http://...first_login=1'

    We should have a pending membership, last workflow actor is not
    the member himself

    >>> mship = team._getOb(mem_id, None)
    >>> mship is None
    False
    >>> wftool.getInfoFor(mship, 'review_state')
    'pending'
    >>> wf_id = wftool.getChainFor(mship)[0]
    >>> history = wftool.getHistoryOf(wf_id, mship)
    >>> history[-1]['actor'] != mem_id
    True

    Log out so we don't interfere w/ later tests
    >>> self.logout()

Verify portal status messages aren't being swallowed
====================================================

    First, let's get an instance of a view that returns a portal
    status message, and redirects

    >>> view = portal.restrictedTraverse('@@login')

    Reset the portal status message
    >>> view.portal_status_message
    [...]
    
    Now setup a pseudo post
    >>> request = view.request
    >>> request.form = dict(__ac_name='m1', login=True)
    >>> request.environ['REQUEST_METHOD'] = 'POST'

    Monkey patch some methods for easier testing
    >>> old_membertool_isanon = view.membertool.isAnonymousUser
    >>> old_update = view.update_credentials
    >>> view.membertool.isAnonymousUser = lambda *a:True
    >>> view.update_credentials = lambda *a:None

    Now we simulate the call to login
    >>> view.handle_login()

    The portal status message should have some data in it now
    >>> len(view.portal_status_message) > 0
    True

    Now restore the original methods
    >>> view.membertool.isAnonymousUser = old_membertool_isanon
    >>> view.update_credentials = old_update

Verify authentication challenges do the right thing
===================================================

Swallow those portal status messages and clear the form

    >>> view.portal_status_message
    [...]
    >>> view.request.form.clear()
    >>> view.request.form
    {}
    >>> oldview = view

Now go to the require_login location

    >>> view = portal.restrictedTraverse('require_login')
    
This is not the view

    >>> view
    <FSPythonScript at /plone/require_login>
    >>> output = view()

This is the old skin which redirects to the login page.

    >>> 'Please sign in to continue.' in output
    True

Remove test_user_1_
===================

Ensure test atomicity by removing the created user:

    >>> self.logout()
    >>> portal.portal_memberdata.manage_delObjects('test_user_1_')
    >>> portal.people.manage_delObjects('test_user_1_')

Is the member still in the catalog?


