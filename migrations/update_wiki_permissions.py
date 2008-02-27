"""
Migration to fix some schizo workflow permissions.
Run this after updating to opencore rXXX
"""

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SpecialUsers import system
import sys
import transaction

newSecurityManager(None, system)

try:
    portal = sys.argv[1]
except IndexError:
    portal = 'openplans'


portal = getattr(app, portal)
setup = portal.portal_setup

profile = 'profile-opencore.configuration:default'
print "Selecting profile %r..." % profile
setup.setImportContext(context_id=profile)
print "Importing workflow..."
result = setup.runImportStep('workflow', run_dependencies=1)
print "Import status messages:"
for key, val in result['messages'].items():
    print "%s\n%s" % (key, "=" * len(key))
    print val or "(no messages)"
    print

# This is one honking big transaction...
workflow = portal.portal_workflow
print "Updating permissions, might take a loong time ..."
workflow.updateRoleMappings()

print "Comitting transaction..."
transaction.commit()
print "OK!"
