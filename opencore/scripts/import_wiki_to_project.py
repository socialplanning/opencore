from Products.CMFCore.utils import getToolByName
from opencore.utils import setup
import transaction
import os, sys
from zipfile import ZipFile

app = setup(app)

zipfile = sys.argv[-2]
project = sys.argv[-1]

project = app.openplans.projects[project]
proj_id = project.getId()

zipfile = ZipFile(zipfile)

import tempfile
tempdir = tempfile.mkdtemp(prefix="--opencore-wiki-import-")

for path in zipfile.namelist():
    parts = path.split("/")
    if len(parts) < 2:
        continue
    if parts[1] == "wiki_history":
        if path.endswith("/"):
            try:
                os.makedirs(os.path.join(tempdir, *parts[2:]))
            except:
                pass
            continue
        else:
            try:
                os.makedirs(os.path.join(tempdir, *parts[2:-1]))
            except:
                pass
        f = zipfile.read(path)
        fp = open(os.path.join(tempdir, *parts[2:]), 'w')
        try:
            fp.write(f)
        finally:
            fp.close()

from sven.bzr import BzrAccess
bzr = BzrAccess(tempdir)

from DateTime import DateTime
repo = getToolByName(project, 'portal_repository')
archivist = getToolByName(project, 'portal_archivist')

PAGES = set()
for revision in reversed(bzr.log("/")):
    path = revision['href']
    timestamp = revision['fields']['timestamp']
    mod_date = DateTime(timestamp)
    user_id = revision['fields']['author']
    commit_message = revision['fields']['message']
    if isinstance(commit_message, unicode):
        commit_message = commit_message.encode("utf8")
    content = bzr.read(path, rev=revision['fields']['version'])

    print "Saving %s, revision %s" % (path, revision['fields']['version'])
    try:
        page_ctx = project[path]
    except KeyError:
        title = path.replace("-", " ").title()
        project.invokeFactory("Document", id=path, title=title)
        page_ctx = project[path]
    PAGES.add(path)

    page_ctx.getField("modification_date").set(page_ctx, mod_date)
    from lxml.html import fromstring, tostring
    try:
        content = tostring(fromstring(content.decode("utf8")))
    except:
        content = ''
    page_ctx.setText(content)

    ## if all goes well this will set lastModifiedAuthor
    from opencore.project.browser.metadata import _update_last_modified_author
    _update_last_modified_author(page_ctx, user_id)
    
    sys_metadata = repo._prepareSysMetadata(commit_message)
    sys_metadata['timestamp'] = mod_date.timeTime()
    prep = archivist.prepare(page_ctx, {}, sys_metadata)
    prep.metadata['sys_metadata']['principal'] = user_id
    archivist.save(prep, autoregister=repo.autoapply)
    prep.copyVersionIdFromClone()

from opencore.nui.wiki.utils import cache_history
for page in PAGES:
    cache_history(project[page], repo)

import shutil
shutil.rmtree(tempdir)

import transaction
transaction.commit()
