from AccessControl.SecurityManagement import newSecurityManager
from opencore.utility.interfaces import IProvideSiteConfig
from Testing.makerequest import makerequest
from zope.component import getUtility
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

configparser = getUtility(IProvideSiteConfig)
portal_id = configparser.get('opencore_site_id')

n = app._getOb(portal_id)
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

steps = {'activate_wicked': dict(),
         'typeinfo': dict(purge_old=True),
         }

# get the custom profile id by assuming that it's the one that
# has 'opencore' in the name but is not 'default'  :-P
ps = n.portal_setup
context_infos = [x['id'] for x in ps.listContextInfos()
                 if 'opencore' in x['id'].lower()]
context_infos = [x for x in context_infos if 'default' not in x]
assert len(context_infos) == 1
profile_id = context_infos[0]

# helpful callable
def run_import_step(setup_tool, step_id, run_deps=False, purge_old=None):
    """ run an import step via the setup tool """
    result = setup_tool.runImportStepFromProfile(profile_id,
                                                 step_id,
                                                 run_dependencies=run_deps,
                                                 purge_old=purge_old,
                                                 )
    print_status_messages(result)

# iterate through the steps
print 'importing selected steps'
for step_id in steps:
    purge = steps.get(step_id).get('purge_old', None)
    run_import_step(ps, step_id, purge_old=purge)
ran_steps = ', '.join(steps.keys())
print 'done importing selected steps: %s' % ran_steps
transaction.get().note('Ran import steps: %s' % ran_steps)
transaction.commit()


# XXX should be populated, key = migration id, value = callable
migrations = dict()

for mig_id in migrations:
    print 'running migration:', mig_id
    migrations[mig_id](portal)
    print 'successfully ran migration:', mig_id

transaction.get().note('Ran migration functions')
transaction.commit()
