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
=======

Get the password reset view. In the future we can plug in a fake mailsender and can do more with this, but it'll do for now::

    >>> view = portal.restrictedTraverse("@@forgot")
    >>> view
    <Products.Five.metaclass.SimpleViewClass from ...>
    >>> request = self.app.REQUEST
    >>> request.environ["REQUEST_METHOD"] = "POST"
    >>> request.set("__ac_name", 'm1')
    >>> view()
    'An email has been sent to you, ...'
        
userexists
==========

See if a username exists::

    >>> request = self.app.REQUEST
    >>> request.set("username", 'someuser')
    >>> view = portal.restrictedTraverse("@@user-exists")
    >>> view.userExists()
    False
    >>> view()
    False
    >>> request.set("username", 'm1')
    >>> view()
    True
