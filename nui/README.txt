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
