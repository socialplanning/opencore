from Products.CMFCore.utils import getToolByName
from opencore.utils import get_config
from sqlalchemy import create_engine

from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker

import os
from datetime import datetime
import subprocess
from sven.bzr import BzrAccess
import shutil

from DateTime import DateTime as zDateTime

def clone(repo, to):
    subprocess.call(["bzr", "checkout", repo, to])
    cwd = os.getcwd()
    os.chdir(to)
    subprocess.call(["bzr", "unbind"])
    os.chdir(cwd)

def get_repo_dir(project):
    opencore_var = os.path.join(get_config("var"), 'opencore')
    repo = get_config("bzr_repos_dir", os.path.join(opencore_var, "bzr_repos"))
    repo = os.path.join(repo, "projects", project.getId(), "main-site", "trunk")
    return repo

def setup_repo(project):
    opencore_var = os.path.join(get_config("var"), 'opencore')

    repo = get_config("bzr_repos_dir", os.path.join(opencore_var, "bzr_repos"))
    repo = os.path.join(repo, "projects", project.getId(), "main-site")

    if os.path.exists(repo):
        shutil.rmtree(repo)
    os.makedirs(repo)

    subprocess.call(["bzr", "init-repo", repo, "--no-trees"])

    repo = os.path.join(repo, "trunk")
    subprocess.call(["bzr", "init", repo])

    checkout = get_config("bzr_checkouts_dir", os.path.join(opencore_var, "bzr_checkouts"))
    checkout = os.path.join(checkout, "projects", project.getId(), "main-site")
    if os.path.exists(checkout):
        shutil.rmtree(checkout)
    os.makedirs(checkout)

    subprocess.call(["bzr", "checkout", "--lightweight", repo, checkout])

    repo = BzrAccess(checkout)
    return repo

def setup_interim_db(project):
    projid = project.getId()

    opencore_var = os.path.join(get_config("var"), 'opencore')
    loc = get_config("tmpdbs", os.path.join(opencore_var, "tmpdbs"))
    loc = os.path.join(loc, projid)

    if os.path.exists(loc):
        os.unlink(loc)
    engine = create_engine("sqlite:///%s.db" % loc, echo=False)
    metadata = MetaData()
    checkin_table = Table(
        "checkins", metadata,
        Column("id", Integer, primary_key=True),
        Column("wikipage", String),
        Column("version", Integer),
        Column("timestamp", DateTime)
        )
    metadata.create_all(engine)
    mapper(Checkin, checkin_table)

    session = sessionmaker(bind=engine)
    return (session(), engine)

class Checkin(object):
    def __init__(self, wikipage, version, timestamp):
        self.wikipage = wikipage
        self.version = version
        self.timestamp = timestamp

    def __repr__(self):
        return "<Checkin #%s for %s>" % (self.version, self.wikipage)

from opencore.interfaces.catalog import ILastModifiedAuthorId
def sort_checkins(project, session=None, db=None):
    pr = getToolByName(project, "portal_repository")
    cat = getToolByName(project, "portal_catalog")

    if session is None or db is None:
        session, db = setup_interim_db(project)
    
    pages = cat.unrestrictedSearchResults(path='/'.join(project.getPhysicalPath()),
                                          portal_type="Document")
    for page in pages:
        ob = page.getObject()
        pagename = ob.getId()

        print "page: %s" % pagename

        versions = pr.getHistory(ob, countPurged=False)
        for version in versions:
            when = datetime.fromtimestamp(version.sys_metadata['timestamp'])
            version_id = version.version_id
            checkin = Checkin(pagename, version_id, when)
            session.add(checkin)
            print "  version: %s" % version_id
        session.commit()

        print "  -* current version *-"
        when = ob.ModificationDate()
        when = zDateTime(when)
        when = when.timeTime()
        when = datetime.fromtimestamp(when)
        version_id = -99
        checkin = Checkin(pagename, version_id, when)
        session.add(checkin)
        session.commit()

def port_checkins(project, session=None, db=None):
    pr = getToolByName(project, "portal_repository")
    cat = getToolByName(project, "portal_catalog")

    if session is None or db is None:
        session, db = setup_interim_db(project)

    opencore_var = os.path.join(get_config("var"), 'opencore')
    repo = get_config("bzr_checkouts_dir", os.path.join(opencore_var, "bzr_checkouts"))
    repo = os.path.join(repo, "projects", project.getId(), "main-site")
    repo = BzrAccess(repo, default_commit_message=" ")

    checkins = session.query(Checkin).order_by(Checkin.timestamp)
    for checkin in checkins:
        pageId = str(checkin.wikipage)
        version = checkin.version

        print "page: %s" % pageId
        try:
            page = project.unrestrictedTraverse(pageId)
        except Exception, e:
            print e
            import pdb; pdb.set_trace()
            continue
        
        if version == -99: # it's the current version
            msg = None
	    content = page.EditableBody()
	    timestamp = zDateTime(page.ModificationDate()).timeTime()
	    author = ILastModifiedAuthorId(page)

        else:
            version = pr.retrieve(page, checkin.version)
            object = version.object
            author = version.sys_metadata['principal']
            msg = version.comment
            content = object.EditableBody()
            timestamp = version.sys_metadata['timestamp']

        print "  rev: %s" % checkin.version

        repo.write(pageId, content, msg=msg,
                   author=author,
                   timestamp=timestamp)
        
#from opencore.utils import setup
#app = setup(app)
#proj = app.openplans.projects['pinguinove']
#import pdb; pdb.set_trace()

#session, db = setup_interim_db(proj)
#sort_checkins(proj, session, db)
#setup_repo(proj)
#port_checkins(proj, session, db)

#project=proj
#pr = getToolByName(project, "portal_repository")
#cat = getToolByName(project, "portal_catalog")

#pages = cat.unrestrictedSearchResults(path='/'.join(project.getPhysicalPath())+'/project-home',
#                                      portal_type="Document")
#page=pages[0].getObject()
#version = pr.retrieve(page, 66)
#
#import pdb; pdb.set_trace()
