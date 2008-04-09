from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
from Products.Five.utilities.marker import erase as noLongerProvides
from itertools import count
from opencore.nui.setup import nui_functions, set_method_aliases
from opencore.nui.wiki import utils
from pprint import pprint 
import sys
import transaction

username = 'admin'
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)
app=makerequest(app)

def print_status_messages(import_result_dict):
    print "Import status messages:"
    for key, val in import_result_dict['messages'].items():
        print "%s\n%s" % (key, "=" * len(key))
        print val or "(no messages)"
        print

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

# for use later
def run_import_step(setup_tool, step_id, run_deps=False):
    """ run an import step via the setup tool """
    result = setup_tool.runImportStep(step_id, run_dependencies=run_deps)
    print_status_messages(result)

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
print 'importing selected steps'
step_ids = ('propertiestool', 'properties', 'workflow')
for step_id in step_ids:
    run_import_step(ps, step_id)
print 'done importing selected steps'
transaction.get().note('Ran import steps: %s' % ', '.join(step_ids))
transaction.commit()


booya_migrations = [
    'Make project home pages relative',
    'Make profile default member page',
    # the annotation already exists; this updates it to what it should be
    'annotate last modified author',
]

for migration in booya_migrations:
    migration_fn = nui_functions[migration]
    print 'running migration:', migration
    migration_fn(portal)
    print 'successfully ran migration:', migration

transaction.get().note('Ran booya setup widgets')
transaction.commit()

print 'updating role mappings'
wft.updateRoleMappings()
print 'done updating role mappings'
transaction.get().note('Updated role mappings')
transaction.commit()

print "Installing portal_geocoder"
qi = portal.portal_quickinstaller
qi.installProducts(['PleiadesGeocoder'])
print "done"
transaction.get().note('Installed portal_geocoder')
transaction.commit()

print "Updating membrane catalog"
run_import_step(ps, 'membranetool')
print "done"
transaction.get().note('membrane_tool reconfigured')
transaction.commit()

print "Reindexing membrane catalog"
portal.membrane_tool.refreshCatalog()
transaction.get().note('membrane_tool reindexed')

transaction.commit()
