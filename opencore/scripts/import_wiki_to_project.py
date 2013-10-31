from Products.CMFCore.utils import getToolByName
from opencore.utils import setup
import transaction
import os, sys
from zipfile import ZipFile
from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest
import simplejson as json

def main(app, zipfile, project):
    user = app.acl_users.getUser('admin')
    print "Changing stuff as user", user
    newSecurityManager(None, user)
    app = makerequest(app)

    project = app.openplans.projects[project]
    proj_id = project.getId()

    zipfile = ZipFile(zipfile)

    import tempfile
    tempdir = tempfile.mkdtemp(prefix="--opencore-wiki-import-")

    wiki_filename_map = {}
    import simplejson

    for path in zipfile.namelist():
        parts = path.split("/")
        if parts[-1] == "wiki_history_filenames.json":
            f = zipfile.read(path)
            wiki_filename_map = simplejson.loads(f)
            continue

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
    i = 0
    for revision in reversed(bzr.log("/")):
        i += 1
        fs_path = revision['href']

        path = wiki_filename_map[fs_path]['filename']

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
            title = wiki_filename_map[fs_path]['title']
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

        if i % 500 == 0:
            transaction.get().commit(True)

    attachment_metadata = json.loads(zipfile.read("%s/attachments.json" % proj_id))

    from StringIO import StringIO
    plone_utils = getToolByName(project, 'plone_utils')

    for path in zipfile.namelist():
        parts = path.split("/")
        if len(parts) < 2:
            continue
        if parts[1] == "pages":
            if len(parts) < 4 or parts[3] == '':
                continue

            metadata = attachment_metadata[path]

            page = parts[2]
            filename = parts[3]
            file = StringIO(zipfile.read(path))
            fileId = filename
            context = project[page]
            context.invokeFactory(id=fileId, type_name="FileAttachment")

            object = context._getOb(fileId, None)
            object.setTitle(metadata['title'] or fileId)
            object.setFile(file)
            
            creation_date = DateTime(metadata['creation_date'])

            object.Schema()['creators'].set(object, (metadata['creator'],))

            object.getField("creation_date").set(object, creation_date)
            object.getField("modification_date").set(object, creation_date) # @@TODO this is getting overwritten with the current date :-(

            object.reindexObject()

    from opencore.nui.wiki.utils import cache_history
    for page in PAGES:
        cache_history(project[page], repo)

    import shutil
    shutil.rmtree(tempdir)


