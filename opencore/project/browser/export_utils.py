from Acquisition import aq_base
from persistent import Persistent
from App import config
from Products.CMFCore.utils import getToolByName
from zc.dict import OrderedDict
from zipfile import ZipFile
import logging
import re
import tempfile
import transaction
import os

_queue_name = 'project_export_queue'

logger = logging.getLogger('opencore.project.export')

badchars = re.compile(r'\W+')


if len(logger.handlers) == 0:
    # Stupid zopectl debug hides my logging.  (or maybe that's good;
    # we do'nt want gunk from other threads?)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)


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
        if getattr(aq_base(self.context.openplans), _queue_name, None) is None:
            setattr(self.context.openplans, _queue_name, OrderedDict())
            transaction.commit()
        self.queue = self.context.openplans[_queue_name]

    def __call__(self):
        for project_id, status in self.queue.iteritems():
            if status.running:
                logger.info('export already in progress for %r' % project_id)
            elif status.failed:
                logger.info('purging old failed job for %r' % project_id)
                del(self.queue[project_id])
            else:
                try:
                    self.context._p_jar.sync()
                    status.start()
                    # XXX need a better persistent locking strategy.
                    # XXX unless we commit here, other threads won't
                    # know it's in progress; and if we do commit, that
                    # means we'd need to somehow detect started but
                    # abandoned jobs, eg. if the server shuts down
                    # mid-job.  Maybe locking should not be
                    # persistent?  If the server restarts, we'll need
                    # to restart the job anyway.
                    self.export(project_id)
                    status.finish()
                    transaction.commit()
                except:
                    transaction.abort()
                    log_exception('Failure in export of project %r:\n' 
                                  % project_id)
                    status.fail()
                    transaction.commit() # just to get the failure note.
                    # XXX Or actually there's no real reason to keep the
                    # job around.  Is there?
        logger.info('Reached end of queue.')
            
    def export(self, project_id):
        proj_dirname = badchars.sub('_', project_id)
        outdir = self._getpath(proj_dirname)
        project = self.context.restrictedTraverse('projects/%s' % project_id)
        catalog = getToolByName(self.context, "portal_catalog")
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
                pagename = badchars.sub('_', page.getId())
                z.writestr("%s/%s.html" % (proj_dirname, pagename), text)
            z.close()
            tmp.close()
        except:
            os.unlink(tmpname)
            raise
        zipname = os.path.join(outdir, proj_dirname + '.zip')
        os.rename(tmpname, zipname)  # Clobber any existing zip.
        self.queue[project_id] = zipname

    def _getpath(self, project_id):
        var = config.getConfiguration().get('clienthome')
        path = os.path.join(var, 'project_exports')
        if not os.path.isdir(path):
            os.makedirs(path)
        return path


class ExportStatus(Persistent):
    # a lightweight bag o' info.

    path = None
    status = None

    __FAILED = 'failed'
    __RUNNING = 'running'
    __DONE = 'done'

    def __init__(self, status=None):
        self.status = status

    @property
    def failed(self):
        return self.status == self.__FAILED

    def failinfo(self):
        return 'XXX more info on what went wrong'

    @property
    def succeeded(self):
        return self.status == self.__DONE

    @property
    def running(self):
        return self.status == self.__RUNNING

    def start(self):
        self.status = self.__RUNNING

    def finish(self):
        self.status = self.__DONE

    def fail(self):
        self.status = self.__FAILED

