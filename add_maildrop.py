from AccessControl.SecurityManagement import newSecurityManager
from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from Products.MailHost.interfaces import IMailHost
from Products.MaildropHost.MaildropHost import MaildropHost
from Testing.makerequest import makerequest
from opencore.utility.interfaces import IProvideSiteConfig
from zope.app.component.hooks import setSite
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

doit = True
mh_obj = getattr(site, mh_id, None)
if isinstance(mh_obj, MaildropHost):
    print 'MaildropHost object already exists at "%s.%s"' % (site_id, mh_id)
    doit = False
elif mh_obj:
    print '%s object already exists at "%s.%s", deleting...' % (mh_obj.__class__, site_id, mh_id)
    site.manage_delObjects([mh_id])

if doit:
    factory = site.manage_addProduct['MaildropHost'].manage_addMaildropHost
    factory(mh_id)
    # Nothing else to configure; MaildropHost reads most of its config from
    # the filesystem.

    transaction.get().note('Replaced old MailHost with a Maildrop Host')
    transaction.commit()
    print "successfully added MaildropHost at", \
          '/'.join(site[mh_id].getPhysicalPath())

# Now we have to make sure the utility registration isn't fuX0red
setSite(site)
mh_obj = getattr(site, mh_id, None)
assert isinstance(mh_obj, MaildropHost)
tool = getToolByName(site, 'MailHost')
if aq_base(tool) is not aq_base(mh_obj):
    sm = site.getSiteManager()
    sm.unregisterUtility(tool, IMailHost)
    sm.registerUtility(mh_obj, IMailHost)
    transaction.get().note('Updated IMailHost utility registration')
    transaction.commit()
    print "successfully updated IMailHost utility registration"
