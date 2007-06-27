====================
 account management
====================

Workflow
========

Test the workflow updating function:: 

    >>> from opencore.nui.setup import install_confirmation_workflow as icw
    >>> from StringIO import StringIO
    >>> out = StringIO()
    >>> icw(portal, out)
    >>> portal.portal_workflow.getChainForPortalType('OpenMember')
    ('openplans_member_confirmation_workflow',)


Forgot Password
===============

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

# test email lookup

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
    Forbidden: You fool! The Internet Police have already been notified of this incident. Your IP has been confiscated.

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
    True

## test do reset


Get Account Confirmation Code
=============================

Get a user so that we can try to get a user's confirmation code for manual registration::

    >>> from Products.CMFCore.utils import getToolByName
    >>> mt = getToolByName(portal, "portal_memberdata")
    >>> user = mt.restrictedTraverse('m1')
    >>> user
    <OpenMember at ...>

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

    >>> view.validate()
    {}
    >>> request.form['confirm_password'] = 'mesty'
    >>> request.form['email'] = 'fakeemail'
    >>> sorted(view.validate().keys())
    ['confirm_password', 'email', 'password']

If you add 'only_validate=True' to the request before submitting
the form the validate() method will be triggered::

    >>> request.form['only_validate'] = True
    >>> view.handle_request()
    u"{...confirm_password...}"

Submit the form for real now; we need to add 'join' to the request::

    >>> request.form['confirm_password'] = 'testy'
    >>> request.form['email'] = 'foobar@example.com'
    >>> del request.form['only_validate']
    >>> request.form['join'] = True
    >>> view.handle_request()

Oh, nothing happened; we need to make the request a POST::
    >>> request.environ["REQUEST_METHOD"] = "POST"
    >>> view.handle_request()
    <OpenMember at /plone/portal_memberdata/foobar>


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

    >>> 'Hey!' in output
    True
