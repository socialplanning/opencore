from AccessControl.SecurityManagement import newSecurityManager
import sys
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

    if len(sys.argv) > 4:
        oc_props = app.openplans.portal_properties.opencore_properties
        oc_props.wordpress_uri = sys.argv[1]
        oc_props.tasktracker_uri = sys.argv[2]
        oc_props.cabochon_uri = sys.argv[3]
        oc_props.twirlip_uri = sys.argv[4]

    transaction.commit()
