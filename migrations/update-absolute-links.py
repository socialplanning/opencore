"""
Finds any absolute links to specific URLs within wiki pages on a site
and edits them to point to a new location.

This script requires the existence of a 'text' index that indexes the
'text' field on site content.  If this index doesn't exist, it will be
created and a reindex will be triggered, which may take a while.
"""

from opencore.upgrades.utils import updateRoleMappings
from AccessControl.SecurityManagement import newSecurityManager
from ZPublisher.HTTPRequest import record

import transaction

username = 'admin'
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)

from Testing.makerequest import makerequest
app=makerequest(app)

portal_id = 'openplans'
portal = app._getOb(portal_id)

# !!! YOU MUST SPECIFY 'FROM' AND 'TO' HOSTS HERE OR THIS SCRIPT WON'T
# DO ANYTHING !!!
old_hosts = []
new_host = ''

cat = portal.portal_catalog
if not 'text' in cat.Indexes:
    extra = record()
    extra.doc_attr = 'getText'
    extra.index_type = 'Cosine Measure'
    extra.lexicon_id = 'plaintext_lexicon'
    cat.addIndex('text', 'ZCTextIndex', extra=extra)
    cat.reindexIndex('text', app.REQUEST)
    transaction.get().note("Added and indexed 'text' index")
    transaction.commit()

pathmap = dict()
for old_host in old_hosts:
    matches = cat(text='href="%s' % old_host, Type='Page')
    for match in matches:
        path = match.getPath()
        if path not in pathmap:
            pathmap[path] = match

commit_interval = 20
i = 0
for match in pathmap.values():
    page = match.getObject()
    text = page.getText()
    for old_host in old_hosts:
        text = text.replace('href="http://%s' % old_host,
                            'href="http://%s' % new_host)
    page.setText(text)
    page.reindexObject(idxs=['text'])
    i += 1
    if i >= commit_interval:
        transaction.get().note('-> Committing %d absolute url replacements' % i)
        transaction.commit()
        i = 0

if i:
    transaction.get().note('-> Committing %d absolute url replacements' % i)
    transaction.commit()
