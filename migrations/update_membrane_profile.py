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

portal.portal_setup.manage_updateToolProperties("profile-opencore.configuration:default", app.REQUEST.RESPONSE)
portal.portal_setup.runImportStep('membranetool')
portal.portal_setup.runImportStep('catalog')
transaction.commit()
