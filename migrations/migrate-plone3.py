from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
from opencore.nui.setup import nui_functions
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

step_ids = ['activate_wicked',
            ]

# get the custom profile id by assuming that it's the one that
# has 'opencore' in the name but is not 'default'  :-P
ps = n.portal_setup
context_infos = [x['id'] for x in ps.listContextInfos()
                 if 'opencore' in x['id'].lower()]
context_infos = [x for x in context_infos if 'default' not in x]
assert len(context_infos) == 1
profile_id = context_infos[0]

# helpful callable
def run_import_step(setup_tool, step_id, run_deps=False):
    """ run an import step via the setup tool """
    result = setup_tool.runImportStepFromProfile(profile_id,
                                                 step_id,
                                                 run_dependencies=run_deps)
    print_status_messages(result)

# iterate through the steps
print 'importing selected steps'
for step_id in step_ids:
    run_import_step(ps, step_id)
print 'done importing selected steps'
transaction.get().note('Ran import steps: %s' % ', '.join(step_ids))
transaction.commit()


migrations = [
]

for migration in migrations:
    migration_fn = nui_functions[migration]
    print 'running migration:', migration
    migration_fn(portal)
    print 'successfully ran migration:', migration

transaction.get().note('Ran migration setup widgets')
transaction.commit()
