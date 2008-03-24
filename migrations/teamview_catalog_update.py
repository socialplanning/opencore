import sys
import transaction
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SpecialUsers import system
from Testing.makerequest import makerequest

def teamview_catalog_update(commit=True):
    newSecurityManager(None, system)
    app=makerequest(app)
    
    try:
        portal = sys.argv[1]
    except IndexError:
        portal = 'openplans'
    
    assert hasattr(app, portal), NameError("No portal '%s' exists" % portal)
    portal = getattr(app, portal)
    
    print "updating membrane catalog"
    setup_tool = portal.portal_setup
    setup_tool.manage_updateToolProperties("profile-opencore.configuration:default",
                                           app.REQUEST.RESPONSE)
    setup_tool.runImportStep('membranetool')
    transaction.get().note('Run membrane_tool profile import step')
    if commit:
        transaction.commit()
    
    print "reindexing membranetool"
    portal.membrane_tool.refreshCatalog()
    transaction.get().note('Reindex membrane_tool ZCatalog')
    if commit:
        transaction.commit()

if __name__ == '__main__':
    teamview_catalog_update()
