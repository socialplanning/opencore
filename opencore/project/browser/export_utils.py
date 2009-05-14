from Acquisition import aq_base
from persistent import Persistent
from App import config
from Products.CMFCore.utils import getToolByName
from zc.dict import OrderedDict
from zipfile import ZipFile
import datetime
import logging
import re
import tempfile
import transaction
import os

_queue_name = 'project_export_queue'

logger = logging.getLogger('opencore.project.export') #XXX

badchars = re.compile(r'\W+')


# if len(logger.handlers) == 0:
#     # Stupid zopectl debug hides my logging.  (or maybe that's good;
#     # we do'nt want gunk from other threads?)
#     logger.addHandler(logging.StreamHandler())
#     logger.setLevel(logging.INFO)


def log_exception(msg='', level=logging.ERROR):
    """Log the most recent exception and traceback
    at the given level (default ERROR).
    """
    # XXX should be in top.utils or some such.
    import StringIO, traceback
    f = StringIO.StringIO()
    traceback.print_exc(file=f)
    msg += f.getvalue()
    logger.log(level=level, msg=msg)


class ProjectExportQueueView(object):

    """Handle a queue of project export jobs which may take a long
    time.  So this is intended to be run often, eg. by
    clockserver. (An event-triggered async job would be nicer for the
    user, but this is probably good enough)
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        # Bootstrap a persistent queue onto the site.
        # XXX move this into an annotation set up via a migration!
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        if getattr(aq_base(portal), _queue_name, None) is None:
            setattr(portal, _queue_name, OrderedDict())
            transaction.commit()
        self.queue = portal[_queue_name]
        self.vardir = config.getConfiguration().clienthome

    def __call__(self):
        for name, status in self.queue.iteritems():
            if status.running:
                logger.info('job already in progress for %r' % name)
                continue
            elif status.failed:
                logger.info('purging old failed job for %r' % name)
                del(self.queue[name])
                continue
            elif status.hung:
                logger.info('purging old hung job for %r' % name)
                # XXX possibly another thread is still chugging on it.
                # What can we do about that?
                # possibly export should be called in a separate
                # zopectl script process instead, and we'd manage PIDs?
                del(self.queue[name])
                continue
            else:
                try:
                    self.context._p_jar.sync()
                    status.start()
                    transaction.commit()
                    self.export(name)
                    status.finish()
                    transaction.get().note('Finished job for %r' % name)
                    transaction.commit()
                except:
                    transaction.abort()
                    status.fail()
                    log_exception('Failure in export of project %r:\n' 
                                  % name)
                    transaction.get().note('Failed job for %r' % name)
                    transaction.commit() # just to get the failure note.
                    # XXX Is there actually any reason to keep the job around?
                    # Maybe failed jobs should be put elsewhere?
        logger.info('Reached end of project export job queue.')
            
    def export(self, project_id):
        """
        the async job should:

        * on any failure, delete the temp file

        * when done, notify (eg. set a PSM for the user w/ download URL)
          and release lock(s).
        """
        proj_dirname = badchars.sub('_', project_id)
        outdir = self._getpath(proj_dirname)
        project = self.context.restrictedTraverse('projects/%s' % project_id)
        catalog = getToolByName(self.context, "portal_catalog")
        zipname = os.path.join(outdir, proj_dirname + '.zip')
        # Using mkstemp instead of other classes in tempfile because I
        # want to rename the file when done w/ it, and only delete on
        # failure.
        tmpfd, tmpname = tempfile.mkstemp(suffix='.zip', dir=outdir)
        tmp = os.fdopen(tmpfd, 'w')   # Dunno why mkstemp returns a file descr.
        try:
            z = ZipFile(tmp, 'w')
            # We want the zip file to contain useful file names; but out
            # of general paranoia for the end user, let's remove
            # potentially evil character sequences before doing so.  (Which
            # hopefully Zope has already done.)
            for page in catalog(portal_type="Document",
                                path='/'.join(project.getPhysicalPath())):
                try:
                    page = page.getObject()
                except AttributeError:
                    logger.warn("Failed to export page at %s; catalog ghost??"
                                % page.getPhysicalPath)
                text = page.getText()
                # XXX appending '.html' will break links!
                z.writestr("%s/%s.html" % (proj_dirname, page.getId()), text)
            z.close()
            tmp.close()
        except:
            try:
                os.unlink(tmpname)
            except:
                pass
            try:
                os.unlink(zipname)
            except:
                pass
            raise
        os.rename(tmpname, zipname)  # Clobber any existing zip.
        return zipname

    def _getpath(self, project_id):
        path = os.path.join(self.vardir, 'project_exports', project_id)
        if not os.path.isdir(path):
            os.makedirs(path)
        return path


class ExportStatus(Persistent):
    # Not even a state machine, just a little bag of info for querying state.

    __FAILED = 'failed'
    __RUNNING = 'running'
    __DONE = 'done'

    # Max time a job can run before we call it hung. XXX will need to
    # try some very large project exports to find a good heuristic.
    maxdelta = datetime.timedelta(hours=6)

    def __init__(self, name, state=None):
        self.name = name
        self.state = state
        self.updatetime = datetime.datetime.utcnow()
        self.starttime = None
        self.path = None

    @property
    def failed(self):
        return self.state == self.__FAILED

    @property
    def failinfo(self):
        return 'XXX more info on what went wrong'

    @property
    def succeeded(self):
        return self.state == self.__DONE

    @property
    def running(self):
        return self.state == self.__RUNNING

    @property
    def hung(self):
        if self.state != self.__RUNNING:
            return False
        now = datetime.datetime.utcnow()
        return now - self.updatetime < self.maxdelta
        # XXX we should also check the zope startup time, if that's
        # possible, and see if that's more recent than self.updatetime

    def start(self):
        self.state = self.__RUNNING
        self.updatetime = self.starttime = datetime.datetime.utcnow()

    def finish(self):
        # XXX fire an event?
        self.state = self.__DONE
        self.updatetime = datetime.datetime.utcnow()

    def fail(self):
        # XXX fire an event?
        self.state = self.__FAILED
        self.updatetime = datetime.datetime.utcnow()
