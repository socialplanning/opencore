from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
from itertools import count
from opencore.nui.setup import set_method_aliases
from opencore.nui.wiki import utils
from opencore.streetswiki.utils import add_wiki
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
print 'importing selected steps'
result = ps.runImportStep('propertiestool', run_dependencies=1)
print_status_messages(result)
result = ps.runImportStep('workflow', run_dependencies=1)
print_status_messages(result)
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

new_site_title = u'Your Streets'
print 'updating the site title to "%s"' % new_site_title
n.setTitle(new_site_title)
print 'site title updated'

email_from_address = 'greetings@yourstreets.org'
print 'setting email from address to "%s"' % email_from_address
n.manage_changeProperties(email_from_address=email_from_address)
print 'set email from address'

print "Adding streetswiki folder"
add_wiki(portal, 'streetswiki', id_='streetswiki')
print "streetswiki folder added"
print
print "Running set_method_aliases widget"
set_method_aliases(portal)
print "done"


print "Installing portal_geocoder"
qi = portal.portal_quickinstaller
qi.installProducts(['PleiadesGeocoder'])
print "done"

print "Running migrate_history..."
path = '/'.join(portal.getPhysicalPath() + ('projects',))
utils.migrate_history(portal, path, out=sys.stdout, save=False)
print "done"


print "Comitting transaction..."
transaction.commit()
print "All migrations done"
