from Acquisition import aq_base
from persistent import Persistent
from App import config
from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IMailingListMessageExport
from Products.listen.interfaces import IMailingListSubscriberExport
from opencore.i18n import _, translate
from zc.dict import OrderedDict
from zipfile import ZipFile
from zope.component import getAdapter
import datetime
import logging
import re
import simplejson as json
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
    # XXX should be in topp.utils or some such.
    import StringIO, traceback
    f = StringIO.StringIO()
    traceback.print_exc(file=f)
    msg += f.getvalue()
    logger.log(level=level, msg=msg)


def get_queue(context):
    # Bootstrap a persistent queue onto the site.
    # XXX move this into an annotation set up via a migration!
    portal = getToolByName(context, 'portal_url').getPortalObject()
    if getattr(aq_base(portal), _queue_name, None) is None:
        setattr(portal, _queue_name, OrderedDict())
        transaction.commit()
    queue = portal[_queue_name]
    return queue

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
        for name, status in self.queue.iteritems():
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
        tmpfd, tmpname = tempfile.mkstemp(suffix='.zip', dir=outdir)
        tmp = os.fdopen(tmpfd, 'w')   # Dunno why mkstemp returns a file descr.
        try:
            z = ZipFile(tmp, 'w')
            self._save_wiki_pages(project, proj_dirname, z)
            status.progress_descr = _(u'Saving Wiki pages')
            transaction.commit()

            self._save_files(project, proj_dirname, z)
            status.progress_descr = _(u'Saving images and file attachments')
            transaction.commit()

            self._save_list_archives(project, proj_dirname, z)
            status.progress_descr = _(u'Saving mailing lists')
            transaction.commit()

            z.close()
            tmp.close()
        except:
            try:
                os.unlink(tmpname)
            except:
                pass
            try:
                os.unlink(outfile_path)
            except:
                pass
            raise
        os.rename(tmpname, outfile_path)  # Clobber any existing of same name.
        return outfile_path


    def _save_wiki_pages(self, project, proj_dirname, azipfile):
        catalog = getToolByName(self.context, "portal_catalog")
        for page in catalog(portal_type="Document",
                            path='/'.join(project.getPhysicalPath())):
            try:
                page = page.getObject()
            except AttributeError:
                logger.warn("Failed to export page at %s; catalog ghost??"
                            % page.getPhysicalPath)
            text = page.getText()
            # XXX appending '.html' will break links!
            azipfile.writestr("%s/pages/%s.html" % (proj_dirname, page.getId()), text)

    def _save_files(self, project, proj_dirname, azipfile):
        from opencore.project.browser.contents import ProjectContentsView
        contents_view = ProjectContentsView(self.context, self.request)
        files = contents_view.files
        for fdict in files:
            obj = self.context.unrestrictedTraverse(fdict['path'])
            out_path = '%s/pages/%s' % (proj_dirname, obj.getId())
            # XXX this will be very bad for big files, since it loads
            # the whole file into memory!  it would be much better to
            # iterate over the horrid pdata chain, writing it to a
            # temp file on disk, and then use
            # azipfile.write(filename).
            azipfile.writestr(out_path, str(obj))
            

    def _save_list_archives(self, project, proj_dirname, azipfile):
        listfol = project['lists']
        for mlistid, mlist in listfol.objectItems(): # XXX filter more?
            # Cargo-culted from listen/browser/import_export.py
            em = getAdapter(mlist, IMailingListMessageExport, name='mbox')
            file_data = em.export_messages() or ''
            mlistid = badchars.sub('_', mlistid)
            azipfile.writestr('%s/lists/%s.mbox' % (proj_dirname, mlistid),
                              file_data)
            # Now the list subscribers.
            es = getAdapter(mlist, IMailingListSubscriberExport, name='csv')
            file_data = es.export_subscribers() or ''
            csv_path = '%s/lists/%s-subscribers.csv' % (proj_dirname, mlistid)
            azipfile.writestr(csv_path, file_data)

        return
        


class ExportStatus(Persistent):
    # Not even a state machine, just a little bag of info for querying state.
    # I kinda wonder if this should just be a dict with magic values.

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
