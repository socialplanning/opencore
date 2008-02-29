username = 'admin'
from AccessControl.SecurityManagement import newSecurityManager
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)
from Testing.makerequest import makerequest
app=makerequest(app)
request = app.REQUEST
import transaction

n = app.openplans
md = n.portal_memberdata
ms = n.portal_membership
uf = n.acl_users
at = n.portal_actions
tt = n.portal_types
wft = n.portal_workflow
cat = n.portal_catalog
tmt = n.portal_teams
# to make it clearer below
portal = n

from opencore.nui.setup import nui_functions

# first, let's set up the default profile

# here's where we get the id of the profile site configuration
ps = n.portal_setup

context_infos = [x['id'] for x in ps.listContextInfos()
                 if 'opencore' in x['id'].lower()]
context_infos = [x for x in context_infos if 'default' not in x]
assert len(context_infos) == 1
context_id = context_infos[0]

# now we set it as the default profile
ps.setImportContext(context_id=context_id)

# and we can import the right steps now
# the true means to run dependencies
print 'importing selected steps'
ps.runImportStep('propertiestool', run_dependencies=1)
result = ps.runImportStep('workflow', run_dependencies=1)
print 'done importing selected steps'

woonerf_migrations = [
    'Initialize Project BTrees',
    'Fix up project home pages',
    'Make project home pages relative',
    'Install Cabochon Client Utility',
    'Make profile default member page',
    'annotate last modified author',
]

for migration in woonerf_migrations:
    migration_fn = nui_functions[migration]
    print 'running migration:', migration
    migration_fn(portal)
    print 'successfully ran migration:', migration

print 'updating role mappings'
wft.updateRoleMappings()
print 'done updating role mappings'

transaction.commit()


## XXX from update_wiki_permissions.py
print "Import status messages:"
for key, val in result['messages'].items():
    print "%s\n%s" % (key, "=" * len(key))
    print val or "(no messages)"
    print

# This is one honking big transaction...
print "Updating permissions, might take a loong time ..."
wft.updateRoleMappings()

print "Comitting transaction..."
transaction.commit()
print "OK!"
