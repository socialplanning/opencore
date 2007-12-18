from AccessControl.SecurityManagement import newSecurityManager
import transaction
from Testing.makerequest import makerequest
app=makerequest(app)

# XXX these should come from config
admin_id = 'admin'
site_id = 'openplans'
site_title = 'Site'

if not site_id in app.objectIds():
    user = app.acl_users.getUser(admin_id)
    user = user.__of__(app.acl_users)
    newSecurityManager(app, user)

    profiles = ('opencore.configuration:default',)
    factory = app.manage_addProduct['CMFPlone'].addPloneSite
    factory(site_id, site_title, extension_ids=profiles)

    transaction.commit()






!DSPAM:4014,47682718224951804284693!
