from AccessControl.SecurityManagement import newSecurityManager
from opencore.configuration.utils import get_config
import sys
import transaction
from Testing.makerequest import makerequest
app=makerequest(app)


admin_file = get_config('general', 'admin_info_filename', default='admin')
admin_id = open(admin_file).read().split(':')[0]
site_id = get_config('general', 'opencore_site_id', default='openplans')
site_id = get_config('general', 'opencore_site_title', default='OpenCore Site')

if not site_id in app.objectIds():
    user = app.acl_users.getUser(admin_id)
    user = user.__of__(app.acl_users)
    newSecurityManager(app, user)

    profiles = ('opencore.configuration:default',)
    factory = app.manage_addProduct['CMFPlone'].addPloneSite
    factory(site_id, site_title, extension_ids=profiles)

    transaction.commit()
