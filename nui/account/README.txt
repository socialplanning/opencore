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

    >>> view.request.set('send', True)
    >>> view.userid

With '__ac_name' set, it should find and confirm a userid::

    >>> view.request.set('__ac_name', 'test_user_1_')
    >>> 
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

Submit the form for real now::

    >>> request.form['confirm_password'] = 'testy'
    >>> request.form['email'] = 'foobar@example.com'
    >>> view.handle_request()

Ah, nothing happened... need to set method to POST::

    >>> request.environ["REQUEST_METHOD"] = "POST"
    >>> view.handle_request()

Ah, nothing happened... need to set button::

    >>> request.set('join', True)
    >>> view.handle_request()
    <OpenMember at /plone/portal_memberdata/foobar>


Confirm
=======

Test the account confirmation view:: (fill this in!)

Calling the view with no key in the request will fail and go to the login page::

    >>> view = portal.restrictedTraverse("@@confirm-account")
    >>> view()
    '...login...'

Get the key for the pending member::
    
    
