import transaction
from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
from opencore.nui.setup import set_method_aliases
from opencore.streetswiki.utils import add_wiki

username = 'admin'
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)
app=makerequest(app)

portal = app.openplans

print "Adding streetswiki folder"
add_wiki(portal, 'streetswiki', id_='streetswiki')
print "streetswiki folder added"
print
print "Running set_method_aliases widget"
set_method_aliases(portal)
print "done"

transaction.get().note('Added streetswiki folder and ran set_method_aliases setup widget')
transaction.commit()
