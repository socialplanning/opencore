from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
from opencore.utility.interfaces import IProvideSiteConfig
from zope.component import getUtility
import transaction

import pdb; pdb.set_trace()

app=makerequest(app)

config = getUtility(IProvideSiteConfig)

admin_file = config.get('admin_info_filename', default='admin')
admin_id = open(admin_file).read().split(':')[0]
site_id = config.get('opencore_site_id', default='openplans')
site_title = config.get('opencore_site_title', default='OpenCore Site')

if not site_id in app.objectIds():
    user = app.acl_users.getUser(admin_id)
    user = user.__of__(app.acl_users)
    newSecurityManager(app, user)

    profiles = ('opencore.configuration:default',)
    factory = app.manage_addProduct['CMFPlone'].addPloneSite
    factory(site_id, site_title, extension_ids=profiles)

    transaction.get().note('Adding openplans site')
    transaction.commit()
