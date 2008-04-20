from AccessControl.SecurityManagement import newSecurityManager
from itertools import count
from opencore.nui.wiki import utils
from pprint import pprint 
import sys
import transaction as txn

username = 'admin'
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)

try:
    portal = sys.argv[1]
except IndexError:
    portal = 'openplans'

try:
    noskip = sys.argv[2]
    noskip = noskip == '--noskip'
except IndexError:
    noskip = False

portal = getattr(app, portal)
path = '/'.join(portal.getPhysicalPath() + ('projects',))

print utils.migrate_history(portal, path, noskip=noskip).getvalue()
