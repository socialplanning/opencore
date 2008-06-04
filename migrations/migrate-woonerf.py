from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
from opencore.nui.setup import nui_functions
from opencore.nui.wiki import utils
#from opencore.streetswiki.utils import add_wiki
#from opencore.nui.setup import set_method_aliases
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


woonerf_migrations = [
    'Initialize Project BTrees',
    'Fix up project home pages',
    'Make project home pages relative',
    'Make profile default member page',
    'annotate last modified author',
    'migrate_listen_container_to_feed',
    'recreate image scales',
    'create square project logos',
]

for migration in woonerf_migrations:
    migration_fn = nui_functions[migration]
    print 'running migration:', migration
    migration_fn(portal)
    print 'successfully ran migration:', migration

transaction.get().note('Ran woonerf setup widgets')
transaction.commit()

print 'updating role mappings'
wft.updateRoleMappings()
print 'done updating role mappings'
transaction.get().note('Updated role mappings')
transaction.commit()

## StreetsWiki deferred from Woonerf release
#print "Adding streetswiki folder"
#add_wiki(portal, 'streetswiki', id_='streetswiki')
#print "streetswiki folder added"
#print
#print "Running set_method_aliases widget"
#set_method_aliases(portal)
#print "done"

print "Installing portal_geocoder"
qi = portal.portal_quickinstaller
qi.installProducts(['PleiadesGeocoder'])
print "done"
transaction.get().note('Installed portal_geocoder')
transaction.commit()

#this needs to run after the other transaction has been run
print "Running migrate_history..."
path = '/'.join(portal.getPhysicalPath() + ('projects',))
utils.migrate_history(portal, path, out=sys.stdout, save=False)
print "done"
transaction.get().note('wiki history migrated')
transaction.commit()
print "migrate_history transaction done"

print "Updating membrane catalog"
run_import_step(ps, 'membranetool')
print "done"
transaction.get().note('membrane_tool reconfigured')
transaction.commit()

print "Reindexing membrane catalog"
portal.membrane_tool.refreshCatalog()
transaction.get().note('membrane_tool reindexed')
transaction.commit()

print "Creating blognetwork page"
portal.invokeFactory('Document', 'blognetwork')
page = portal.blognetwork
page.setTitle(u'Blog Network')
page.setText(u'<p>Blog network text goes here</p>')
page.reindexObject()
transaction.get().note('added blognetwork page to portal')
transaction.commit()

print "Creating sw template page"
portal.invokeFactory('Document', 'sw-template')
page = portal._getOb('sw-template')
page.setTitle(u'StreetsWiki Template')
page.setText(u'<p>Default streetswiki template goes here</p>')
page.reindexObject()
transaction.get().note('added streetswiki template page to portal')
transaction.commit()
