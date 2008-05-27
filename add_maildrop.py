from AccessControl.SecurityManagement import newSecurityManager
from Products.MaildropHost.MaildropHost import MaildropHost
from Testing.makerequest import makerequest
from opencore.utility.interfaces import IProvideSiteConfig
from zope.component import getUtility
import sys
import transaction

app=makerequest(app)

config = getUtility(IProvideSiteConfig)

mh_id = 'MailHost'
site_id = config.get('opencore_site_id', default='openplans')
admin_file = config.get('admin_info_filename', default='admin')
admin_id = open(admin_file).read().split(':')[0]

# Change the effective user... dunno if it matters, but nice for undo log.
user = app.acl_users.getUser(admin_id)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)

site = app[site_id]

mh_obj = getattr(site, mh_id, None)
if mh_obj and isinstance(mh_obj, MaildropHost):
    print 'MaildropHost object already exists at "%s.%s", exiting...' % (site_id, mh_id)
    sys.exit()

factory = site.manage_addProduct['MaildropHost'].manage_addMaildropHost
factory(mh_id)
# Nothing else to configure; MaildropHost reads most of its config from
# the filesystem.

transaction.get().note('Replacing old MailHost with a Maildrop Host')
transaction.commit()
print "successfully added MaildropHost at", \
      '/'.join(site[mh_id].getPhysicalPath())
