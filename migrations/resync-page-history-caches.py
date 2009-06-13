username = 'admin'
from AccessControl.SecurityManagement import newSecurityManager
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)
from Testing.makerequest import makerequest
app=makerequest(app)
import transaction
from zope.app.component.hooks import setSite
from opencore.nui.wiki.interfaces import IWikiHistory

n = app.openplans
setSite(n)
cat = n.portal_catalog

batch = 200
page_brains = cat(Type='Page')
i = 0
for page_brain in page_brains:
    page = page_brain.getObject()
    try:
        cache = IWikiHistory(page)
    except TypeError:
        # couldn't adapt, we don't cache history, skip it
        continue
    cache.resync_history_cache()
    i += 1
    if i == batch:
        transaction.get().note('incremental page history sync commit: %d'
                               % batch)
        transaction.commit()
        i = 0
transaction.get().note('final page history sync commit: %d' % i)
transaction.commit()
