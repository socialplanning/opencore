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
from logging import getLogger, INFO

logger = getLogger('opencore.resync-page-history-caches')

n = app.openplans
setSite(n)
cat = n.portal_catalog

batch = 200
page_brains = cat(Type='Page')
i = 0
for page_brain in page_brains:
    try:
        page = page_brain.getObject()
    except AttributeError:
        # catalog ghost... might as well clear it out
        cat._catalog.uncatalogObject(page_brain.getPath())
        continue
    try:
        cache = IWikiHistory(page)
    except TypeError:
        # couldn't adapt, we don't cache history, skip it
        continue
    cache.resync_history_cache()
    logger.log(INFO, '%s history cache updated' % page_brain.getPath())
    i += 1
    if i == batch:
        msg = 'incremental page history sync commit: %d' % batch
        transaction.get().note(msg)
        transaction.commit()
        logger.log(INFO, msg)
        i = 0

transaction.get().note('final page history sync commit: %d' % i)
transaction.commit()
logger.log(INFO, 'FINISHED!')
