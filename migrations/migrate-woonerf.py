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


## from cache_version_history.py
pc = portal.portal_catalog
pr = portal.portal_repository
path = '/'.join(portal.getPhysicalPath() + ('projects',))
brains = pc(portal_type="Document", path=path)

print "\nattempting to migrate %s @ %s" %(len(brains), path)

counter = count()
skipcounter = count()
_ghosts = []
entries = 0

try:
    for brain in brains:
        try:
            page = brain.getObject()
        except AttributeError:
            # kill ghost
            skipcounter.next()
            _ghosts.append(brain.getPath())
            pc.uncatalog_object(brain.getPath())
            # transaction.commit()
            continue
        
        page._p_jar.sync()
        if getattr(page, '__HISTORY_MIGRATED__', False):
            skipcounter.next()
            continue

        result = utils.cache_history(page, pr)
        mcount = scount = 0
        
        if result:
            # transaction.commit()
            mcount = counter.next()
            entries += result
        elif result is False:
            scount = skipcounter.next()
        elif result == 0:
            print "no history: %s" %brain.getPath()
            
        i = mcount + scount
        if i and not i % 100:
            print "%s docs migrated" %i
            
except KeyboardInterrupt, e:
    print e

print
print "Total pages migrated: % 3s" %(counter.next() - 1)
print "Total entries migrated: % 1s" %(entries) 
print "Total skipped: % 10s" %(skipcounter.next() - 1)
print "Total ghosts removed: % 3s" %len(_ghosts)
if _ghosts:
    pprint(_ghosts)



print "Comitting transaction..."
transaction.commit()
print "All migrations done"
