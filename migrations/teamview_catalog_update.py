import transaction
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SpecialUsers import system
from Testing.makerequest import makerequest

newSecurityManager(None, system)
app=makerequest(app)

try:
    portal = sys.argv[1]
except IndexError:
    portal = 'openplans'

assert hasattr(app, portal), NameError("No portal %s exists" %portal)
portal = getattr(app, portal)

print "updating membrane catalog"
setup_tool = portal.portal_setup
setup_tool.manage_updateToolProperties("profile-opencore.configuration:default",
                                       app.REQUEST.RESPONSE)
setup_tool.runImportStep('membranetool')
transaction.get().note('Run membrane_tool profile import step')
transaction.commit()

print "reindexing membranetool"
portal.membrane_tool.refreshCatalog()
transaction.get().note('Reindex membrane_tool ZCatalog')
transaction.commit()
