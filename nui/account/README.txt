====================
 account management
====================

workflow
========

Test the workflow updating function::

    >>> from Products.OpenPlans.Extensions.Install import install_confirmation_workflow as icw
    >>> from StringIO import StringIO
    >>> out = StringIO()
    >>> portal.portal_workflow.getChainForPortalType('OpenMember')
    ('openplans_member_workflow',)
    >>> icw(portal, out)
    >>> portal.portal_workflow.getChainForPortalType('OpenMember')
    ('openplans_member_confirmation_workflow',)


password reset
==============

Get the password reset view. In the future we can plug in a fake mailsender and can do more with this, but it'll do for now::

    >>> view = portal.restrictedTraverse("@@forgot")
    >>> view
    <Products.Five.metaclass.SimpleViewClass from ...>
    >>> request = self.app.REQUEST
    >>> request.environ["REQUEST_METHOD"] = "POST"
    >>> request.set("__ac_name", 'm1')
    >>> view()
    'An email has been sent to you, ...'
        

get account confirmation code
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

join
====

Test the join view by adding a member to the site:

    >>> view = portal.restrictedTraverse("@@join")
    >>> request = view.request

    >>> form = dict(id='foobar',
    ...             email='foobar@example.com',
    ...             password= 'testy',
    ...             confirm_password='testy')
    >>> request.form.update(form)
    >>> view.handle_request()

Ah, nothing happened... need to set method to POST::

    >>> request.environ["REQUEST_METHOD"] = "POST"
    >>> view.handle_request()

Ah, nothing happened... need to set button::

    >>> request.set('join', True)
    >>> view.handle_request()
    <OpenMember at /plone/portal_memberdata/openmember...>
