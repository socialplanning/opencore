from App import config
from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IMailingListMessageExport
from Products.listen.interfaces import IMailingListSubscriberExport
from opencore.i18n import _, translate
from pkg_resources import resource_stream
from zipfile import ZipFile
from zope.app.component.hooks import setSite
from zope.component import getAdapter
import datetime
import logging
import os
import re
import simplejson as json
import tempfile
import time
import transaction


TEMP_PREFIX='temp_project_export'

TEST=False

logger = logging.getLogger('opencore.project.export') #XXX

badchars = re.compile(r'\W+')


def log_exception(msg='', level=logging.ERROR):
    """Log the most recent exception and traceback
    at the given level (default ERROR).
    """
    # XXX should be in topp.utils or some such.
    import StringIO, traceback
    f = StringIO.StringIO()
    traceback.print_exc(file=f)
    msg += f.getvalue()
    logger.log(level=level, msg=msg)


_queue = None
def get_queue(context):
    # We don't use a persistent queue because there's no meaningful way
    # to resume a job interrupted by eg. server restart.
    # A global will work fine for shared state.
    from topp.utils.orderedpersistentmapping import SortedDict
    global _queue
    if _queue is None:
        _queue = SortedDict()
    return _queue

def readme():
    text = resource_stream('opencore.project.browser', 'export_readme.txt').read()
    return text


class ProjectExportQueueView(object):

    """Handle a queue of project export jobs which may take a long
    time.  So this is intended to be run often, eg. by
    clockserver. (An event-triggered async job would be nicer for the
    user, but this is probably good enough)
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.queue = get_queue(self.context)
        self.vardir = config.getConfiguration().clienthome

    def __call__(self):
        count = len(self.queue)
        for name, status in self.queue.items():
            if status.running:
                logger.info('job already in progress for %r' % name)
                continue
            elif status.failed:
                logger.info('purging old failed job for %r' % name)
                del(self.queue[name])
                continue
            elif status.succeeded:
                logger.info('purging old finished job for %r' % name)
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
                    status.start()
                    transaction.commit()
                    outfile_path = self.export(name, status)
                    status.finish(outfile_path)
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
        if count:
            logger.info('Reached end of project export job queue (%d items)'
                        % count)
            
    def export(self, project_id, status=None):
        """
        the async job should:

        * on any failure, delete the temp file

        * when done, notify (eg. set a PSM for the user w/ download URL)
          and release lock(s).
        """
        # We want the zip file to contain useful file names; but out
        # of general paranoia for the end user, let's remove
        # potentially evil character sequences before doing so.  (Which
        # hopefully Zope has already done.)
        if status is None:
            status = ExportStatus(project_id)
        proj_dirname = badchars.sub('_', project_id)
        outdir = getpath(project_id, self.vardir)
        project = self.context.restrictedTraverse('projects/%s' % project_id)
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d_%H:%M:%S')
        outfile_path = os.path.join(outdir, '%s-%s.zip' % (proj_dirname, timestamp))
        # Using mkstemp instead of other classes in tempfile because I
        # want to rename the file when done w/ it, and only delete on
        # failure.
        tmpfd, tmpname = tempfile.mkstemp(suffix='.zip', prefix=TEMP_PREFIX, dir=outdir)
        tmp = os.fdopen(tmpfd, 'w')   # Dunno why mkstemp returns a file descr.
        try:
            z = ZipFile(tmp, 'w')
            exporter = ContentExporter(project, self.request, status, proj_dirname, z)
            exporter.save()
            z.close()
            tmp.close()
        except:
            if os.path.exists(tmpname):
                os.unlink(tmpname)
            if os.path.exists(outfile_path):
                os.unlink(outfile_path)
            raise
        os.rename(tmpname, outfile_path)  # Clobber any existing of same name.
        return outfile_path


class ContentExporter(object):

    def __init__(self, context, request, status, context_dirname, azipfile):
        self.context = context
        self.request = request
        self.status = status
        self.context_dirname = context_dirname
        self.zipfile = azipfile

    def save(self):
        if TEST:
            # For interactive testing, it's useful to be able to slow
            # things down and watch progress.
            sleep = lambda: time.sleep(5)
        else:
            sleep = lambda: None
        self.save_docs()
        sleep()
        self.save_wiki_pages()
        sleep()
        self.save_files()
        sleep()
        self.save_list_archives()
        sleep()

    def save_docs(self):
        self.status.progress_descr = _(u'Saving documentation')
        self.zipfile.writestr("%s/README.txt" % self.context_dirname, readme())

    def save_wiki_pages(self):
        self.status.progress_descr = _(u'Saving Wiki pages')
        catalog = getToolByName(self.context, "portal_catalog")
        for page in catalog(portal_type="Document",
                            path='/'.join(self.context.getPhysicalPath())):
            try:
                page = page.getObject()
            except AttributeError:
                logger.warn("Failed to export page at %s; catalog ghost??"
                            % page.getPhysicalPath)
            text = page.getText()
            # XXX appending '.html' will break links!
            self.zipfile.writestr("%s/pages/%s.html" % (self.context_dirname, 
                                                        page.getId()), text)

    def save_files(self):
        self.status.progress_descr = _(u'Saving images and file attachments')
        from opencore.project.browser.contents import ProjectContentsView
        contents_view = ProjectContentsView(self.context, self.request)
        files = contents_view.files
        for fdict in files:
            obj = self.context.unrestrictedTraverse(fdict['path'])
            out_path = '%s/pages/%s' % (self.context_dirname, obj.getId())
            # XXX this will be very bad for big files, since it loads
            # the whole file into memory!  it would be much better to
            # iterate over the horrid pdata chain, writing it to a
            # temp file on disk, and then use
            # azipfile.write(filename).
            self.zipfile.writestr(out_path, str(obj))
            

    def save_list_archives(self):
        self.status.progress_descr = _(u'Saving mailing lists')
        listfol = self.context['lists']
        for mlistid, mlist in listfol.objectItems(): # XXX filter more?
            setSite(mlist)  # Needed to get the export adapter.
            # Cargo-culted from listen/browser/import_export.py
            em = getAdapter(mlist, IMailingListMessageExport, name='mbox')
            file_data = em.export_messages() or ''
            mlistid = badchars.sub('_', mlistid)
            self.zipfile.writestr('%s/lists/%s.mbox' % (self.context_dirname, mlistid),
                                  file_data)
            # Now the list subscribers.
            es = getAdapter(mlist, IMailingListSubscriberExport, name='csv')
            file_data = es.export_subscribers() or ''
            csv_path = '%s/lists/%s-subscribers.csv' % (self.context_dirname, mlistid)
            self.zipfile.writestr(csv_path, file_data)
        


class ExportStatus(object):
    # Not even a state machine, just a little bag of info for querying state.
    # I kinda wonder if this should just be a dict with some conventions.

    QUEUED = 'queued, waiting to start'
    RUNNING = 'running'
    DONE = 'finished'
    FAILED = 'failed'
    NULL = 'no job running'

    # Max time a job can run before we call it hung. XXX will need to
    # try some very large project exports to find a good heuristic.
    maxdelta = datetime.timedelta(hours=6)

    def __init__(self, name, state=None):
        self.name = name
        self.state = state or self.NULL
        self.updatetime = datetime.datetime.utcnow()
        self.starttime = None
        self.path = None
        self.filename = None
        self.progress_descr = _(u'') # More detailed human-readable state info.

    @property
    def failed(self):
        return self.state == self.FAILED

    @property
    def succeeded(self):
        return self.state == self.DONE

    @property
    def running(self):
        return self.state == self.RUNNING

    @property
    def queued(self):
        return self.state == self.QUEUED

    @property
    def active(self):
        return self.running or self.queued

    @property
    def hung(self):
        if self.state != self.RUNNING:
            return False
        now = datetime.datetime.utcnow()
        return now - self.updatetime < self.maxdelta
        # XXX we should also check the zope startup time, if that's
        # possible, and see if that's more recent than self.updatetime

    def start(self):
        self.state = self.RUNNING
        self.updatetime = self.starttime = datetime.datetime.utcnow()

    def finish(self, path):
        # XXX fire an event?
        self.path = path
        self.filename = os.path.basename(path)
        self.state = self.DONE
        self.progress_descr = _(u'Export finished')
        self.updatetime = datetime.datetime.utcnow()

    def fail(self):
        # XXX fire an event?
        self.state = self.FAILED
        self.progress_descr = _(u'Export failed!')
        self.updatetime = datetime.datetime.utcnow()

    def json(self):
        result = {
            'state': self.state, #XXX should i18n these?
            'filename': self.filename,
            'progress': translate(self.progress_descr),
            }
        return json.dumps(result)


def getpath(project_id, vardir=None):
    if vardir is None:
        vardir = config.getConfiguration().clienthome
    proj_dirname = badchars.sub('_', project_id)
    path = os.path.join(vardir, 'project_exports', project_id)
    if not os.path.isdir(path):
        os.makedirs(path)
    return path
