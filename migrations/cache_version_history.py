from AccessControl.SecurityManagement import newSecurityManager
from opencore.nui.wiki import utils
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
    if noskip == '--noskip':
        noskip = True
except IndexError:
    noskip = False

portal = getattr(app, portal)

prt_pth = portal.getPhysicalPath()
path = ['/'.join(prt_pth + (seg ,)) for seg in 'people', 'projects',]

print utils.migrate_history(portal, path, noskip=noskip).getvalue()


