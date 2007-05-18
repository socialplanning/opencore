====================
 account management
====================

workflow
========

Test the workflow updating function::

    >>> from Products.OpenPlans.Extensions.Install import install_confirmation_workflow as icw
    >>> from StringIO import StringIO
    >>> out = StringIO()
    >>> icw(portal, out)
    >>> portal.portal_workflow.getChainForPortalType('OpenMember')
    ('openplans_member_confirmation_workflow',)


Tests opencore view
===================

See if a username exists:

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
