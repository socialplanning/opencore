# Prints all Listen lists and their addresses.
# Meant to be run via 'zopectl run'

portal = app.openplans

brains = portal.portal_catalog.unrestrictedSearchResults(Type='Open Mailing Lis\
t')

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.User import UnrestrictedUser
newSecurityManager(None, UnrestrictedUser('god', '', ['Manager'], ''))

results	= []
for b in brains:
    list_id = b.getId
    mlist = b.getObject()
    list_addr =	mlist.mailto
    results.append((list_id, list_addr))

import pprint
pprint.pprint(sorted(results))

