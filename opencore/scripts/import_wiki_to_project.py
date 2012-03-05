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

for revision in reversed(bzr.log("/")):
    path = revision['href']
    timestamp = revision['fields']['timestamp']
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
    
    from lxml.html import fromstring, tostring
    try:
        content = tostring(fromstring(content.decode("utf8")))
    except:
        content = ''

    page_ctx.setText(content)
    ## TODO: notify ObjectModifiedEvent?

    repo = getToolByName(page_ctx, 'portal_repository')
    repo.save(page_ctx, comment=commit_message)

import shutil
shutil.rmtree(tempdir)

import transaction
transaction.commit()
