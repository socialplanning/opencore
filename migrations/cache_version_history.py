from pprint import pprint 
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SpecialUsers import system
from opencore.nui.wiki import utils
import sys
import transaction as txn

newSecurityManager(None, system)

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

path = '/'.join(portal.getPhysicalPath() + ('projects',))

print utils.migrate_history(portal, path, noskip=noskip).getvalue()


