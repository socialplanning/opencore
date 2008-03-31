from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
from opencore.configuration.utils import get_config
import transaction

app=makerequest(app)

mh_id = 'MailHost'
site_id = get_config('general', 'opencore_site_id', default='openplans')
admin_file = get_config('general', 'admin_info_filename', default='admin')
admin_id = open(admin_file).read().split(':')[0]

# Change the effective user... dunno if it matters, but nice for undo log.
user = app.acl_users.getUser(admin_id)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)

site = app[site_id]

if mh_id in site.objectIds():
    # We might have run this script already. Or it might be a vanilla
    # MailHost.  Either way, easiest to just wipe it and make a new
    # one.
    site.manage_delObjects([mh_id])

factory = site.manage_addProduct['MaildropHost'].manage_addMaildropHost
factory(mh_id)
# Nothing else to configure; MaildropHost reads most of its config from
# the filesystem.

transaction.commit()
print "successfully added MaildropHost at", \
      '/'.join(site[mh_id].getPhysicalPath())
