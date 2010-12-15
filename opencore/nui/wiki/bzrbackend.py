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

def setup_repo(project):
    repo = get_config("bzr_repos_dir")
    repo = os.path.join(repo, "projects", project.getId())

    if not os.path.exists(repo):
        os.makedirs(repo)
    subprocess.call(["bzr", "init", repo])

    repo = BzrAccess(repo)
    return repo

def setup_interim_db(project):
    projid = project.getId()
    loc = get_config("tmpdbs")
    loc = os.path.join(loc, projid)
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


def sort_checkins(project):
    pr = getToolByName(project, "portal_repository")
    cat = getToolByName(project, "portal_catalog")

    session, db = setup_interim_db(project)
    
    pages = cat.unrestrictedSearchResults(path='/'.join(project.getPhysicalPath()),
                                          portal_type="Document")
    for page in pages:
        ob = page.getObject()
        pagename = ob.getId()
        versions = pr.getHistory(ob, countPurged=False)
        for version in versions:
            when = datetime.fromtimestamp(version.sys_metadata['timestamp'])
            version_id = version.version_id
            checkin = Checkin(pagename, version_id, when)
            session.add(checkin)
        session.commit()

def port_checkins(project):
    pr = getToolByName(project, "portal_repository")
    cat = getToolByName(project, "portal_catalog")

    session, db = setup_interim_db(project)

    repo = get_config("bzr_repos_dir")
    repo = os.path.join(repo, "projects", project.getId())
    repo = BzrAccess(repo)

    checkins = session.query(Checkin).order_by(Checkin.timestamp)
    for checkin in checkins:
        pageId = checkin.wikipage
        page = project[pageId]
        version = pr.retrieve(page, checkin.version)
        author = version.sys_metadata['principal']
        msg = version.comment
        content = version.object.EditableBody()
        revprops = {'opencore.author': author,
                    'opencore.timestamp': str(version.sys_metadata['timestamp'])}
        repo.write(pageId, content, msg=msg,
                   revprops=revprops)
        
from opencore.utils import setup
app = setup(app)
#proj = app.openplans.projects.moo
#sort_checkins(proj)
#port_checkins(proj)
import pdb; pdb.set_trace()
