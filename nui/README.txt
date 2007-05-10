Tests opencore view
===================

See if a username exists:

   >>> request = self.app.REQUEST
   >>> request.set("username", 'someuser')
   >>> view = self.portal.restrictedTraverse("@@user-exists")
   >>> view.userExists()
   False
   >>> view()
   False
   >>> request.set("username", 'm1')
   >>> view()
   True



Tests projects view
===================

Let's get a view for the projects list page
    >>> view = self.portal.restrictedTraverse('oc-projects')
    >>> view
    <Products.Five.metaclass.SimpleViewClass from ...>

Call it to get a page back
    >>> response = view()

Check to see that some expected strings are in there. Flunc tests?
    >>> exp = ['Projects on OpenPlans', 'Search for projects',
    ...        'Recently updated projects', 'Featured projects']
    >>> for s in exp:
    ...     assert s in response

