from App import config
from datetime import datetime
from DateTime import DateTime as zDateTime
import logging
from opencore.interfaces.catalog import ILastModifiedAuthorId
from opencore.utils import get_config
import os
import pickle
import cPickle
from Products.CMFCore.utils import getToolByName
import shutil
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker
import subprocess
from sven.bzr import BzrAccess
from ZODB.POSException import POSKeyError
logger = logging.getLogger('opencore.export')

def clone(repo, to):
    subprocess.call(["bzr", "checkout", repo, to])
    cwd = os.getcwd()
    os.chdir(to)
    subprocess.call(["bzr", "unbind"])
    os.chdir(cwd)

def get_repo_dir(project, basedir=None):
    if basedir is None:
        basedir = get_config("bzr_repos_dir", None)
    if basedir is None:
        vardir = config.getConfiguration().clienthome
        basedir = os.path.join(vardir, "bzr_repos")

    repo = os.path.join(basedir,
                        "projects", project.getId(),
                        "main-site", "trunk")
    return repo

class WikiConverter(object):

    def __init__(self, project, 
                 tmpdbdir, repodir, checkoutdir, namespace="projects"):
        self.project = project
        projid = project.getId()

        self.tmpdb = os.path.join(tmpdbdir, projid)
        self.repodir = os.path.join(
            repodir, namespace, projid, "main-site")
        self.repotrunk = os.path.join(
            self.repodir, "trunk")
        self.checkoutdir = os.path.join(
            checkoutdir, namespace, projid, "main-site")

        self.session = None
        self.db = None

        portal = getToolByName(project, 'portal_url').getPortalObject()
        self.committer = portal.getProperty('email_from_address')

    def reset(self):
        if os.path.exists(self.repodir):
            shutil.rmtree(self.repodir)
        os.makedirs(self.repodir)
        if os.path.exists(self.checkoutdir):
            shutil.rmtree(self.checkoutdir)
        os.makedirs(self.checkoutdir)
        if os.path.exists(self.tmpdb):
            os.unlink(self.tmpdb)
        dirname = os.path.dirname(self.tmpdb)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if self.session is not None:
            del self.session
            self.session = None
        if self.db is not None:
            del self.db
            self.db = None

    def unbind_checkout(self):
        to = self.checkoutdir
        cwd = os.getcwd()
        os.chdir(to)
        subprocess.call(["bzr", "unbind"])
        os.chdir(cwd)

    def convert(self):
        self.reset()
        self.setup_interim_db()
        self.sort_checkins()
        self.setup_repo()
        filename_map = self.port_checkins()
        self.unbind_checkout()
        return self.checkoutdir, filename_map

    def setup_interim_db(self):
        engine = create_engine("sqlite:///%s.db" % 
                               self.tmpdb, echo=False)
        metadata.create_all(engine)

        session = sessionmaker(bind=engine)
        self.session = session()
        self.db = engine

    def setup_repo(self):
        subprocess.call(["bzr", "init-repo", 
                         self.repodir, "--no-trees"])
        subprocess.call(["bzr", "init", self.repotrunk])
        subprocess.call(["bzr", "checkout",
                         self.repotrunk,
                         self.checkoutdir])
        repo = BzrAccess(self.checkoutdir)
        return repo
    
    def sort_checkins(self):
        project = self.project
        pr = getToolByName(project, "portal_repository")
        cat = getToolByName(project, "portal_catalog")

        session = self.session
        db = self.db

        proj_id = project.getId()

        pages = cat.unrestrictedSearchResults(path='/'.join(project.getPhysicalPath()),
                                              portal_type="Document")
        for page in pages:
            ob = page.getObject()
            pagename = ob.getId()

            logger.info("page: %s" % pagename)

            versions = pr.getHistory(ob, countPurged=False)
            try:
                for version in versions:
                    when = datetime.fromtimestamp(version.sys_metadata['timestamp'])
                    version_id = version.version_id
                    print proj_id, page.getId, version_id
                    checkin = Checkin(pagename, version_id, when)
                    session.add(checkin)
                    logger.info("page: %s\tversion: %s" % (pagename, version_id))
                session.commit()
            except (cPickle.UnpicklingError, pickle.UnpicklingError, POSKeyError), e:
                logger.error("Corruption error on page %s in project %s: %s" % (
                        pagename, project.getId(), str(e)))
                fp = open("/tmp/unpickle.txt", 'wa')
                print >> fp, "Corruption error on page %s in project %s: %s" % (
                    pagename, project.getId(), str(e))
                fp.close()

            logger.info("page: %s\t-* current version *-" % pagename)
            when = ob.ModificationDate()
            when = zDateTime(when)
            when = when.timeTime()
            when = datetime.fromtimestamp(when)
            version_id = -99
            checkin = Checkin(pagename, version_id, when)
            session.add(checkin)
            session.commit()

    def port_checkins(self):
        project = self.project
        pr = getToolByName(project, "portal_repository")
        cat = getToolByName(project, "portal_catalog")

        session = self.session
        db = self.db
        checkout = self.checkoutdir

        repo = BzrAccess(checkout, default_commit_message=" ")
        
        checkins = session.query(Checkin).order_by(Checkin.timestamp)
        filename_map = {}

        for checkin in checkins:
            pageId = str(checkin.wikipage)
            version = checkin.version

            logger.info("page: %s" % pageId)
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

            logger.info("page: %s\trev: %s" % (page, checkin.version))

            try:
                repo.write(pageId, content, msg=msg,
                           author=author,
                           committer=self.committer,
                           timestamp=timestamp)
                filename_map[pageId] = {"id": pageId, "filename": pageId,
                                        "title": page.Title()}
            except IOError, e:
                if e.errno == 36:
                    import md5
                    hashedId = md5.md5(pageId).hexdigest()
                    repo.write(hashedId,
                               content, msg=msg,
                               author=author,
                               committer=self.committer,
                               timestamp=timestamp)
                    filename_map[pageId] = {"id": pageId, "filename": hashedId,
                                            "title": page.Title()}
                else:
                    raise
        return filename_map


class Checkin(object):
    def __init__(self, wikipage, version, timestamp):
        self.wikipage = wikipage
        self.version = version
        self.timestamp = timestamp

    def __repr__(self):
        return "<Checkin #%s for %s>" % (self.version, self.wikipage)
metadata = MetaData()
checkin_table = Table(
    "checkins", metadata,
    Column("id", Integer, primary_key=True),
    Column("wikipage", String),
    Column("version", Integer),
    Column("timestamp", DateTime)
    )
mapper(Checkin, checkin_table)
        
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
