from App import config
from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IMailingListMessageExport
from Products.listen.interfaces import IMailingListSubscriberExport
from Products.listen.interfaces import IMembershipList
from Products.listen.lib.common import lookup_member_id
from Queue import Queue, Empty
from opencore.i18n import _, translate
from opencore.utility.interfaces import IHTTPClient
from opencore.utility.interfaces import IProvideSiteConfig
from pkg_resources import resource_stream
from topp.featurelets.interfaces import IFeatureletSupporter
from topp.featurelets.supporter import IFeaturelet
from zipfile import ZipFile
from zope.app.component.hooks import setSite
from zope.component import getAdapter
from zope.component import getAdapters
from zope.component import getUtility
import StringIO
import datetime
import logging
import os
import re
import simplejson as json
import tempfile
import threading
import time
import traceback
import transaction

TEMP_PREFIX='temp_project_export'

# For interactive testing, it's useful to be able to slow things down
# and watch progress.
TEST_SLEEPTIME=0

logger = logging.getLogger('opencore.project.browser')

badchars = re.compile(r'\W+')


def log_exception(msg='', level=logging.ERROR):
    """Log the most recent exception and traceback
    at the given level (default ERROR).
    """
    # XXX should be in topp.utils or some such.
    f = StringIO.StringIO()
    traceback.print_exc(file=f)
    msg += f.getvalue()
    logger.log(level=level, msg=msg)


_status_lock = threading.Lock()
_status_dict = {}

def get_status(name, cookie='', context_url=''):
    """ Get or create an ExportStatus instance for the given identifier."""
    _status_lock.acquire()
    try:
        if name not in _status_dict:
            _status_dict[name] = ExportStatus(name, context_url=context_url,
                                              cookie=cookie)
        return _status_dict[name]
    finally:
        _status_lock.release()


_queue = Queue()
def get_queue():
    # We don't use a persistent queue because there's no meaningful way
    # to resume a job interrupted by eg. server restart.
    # A global will work fine for shared state.
    return _queue

def readme():
    text = resource_stream('opencore.project.browser', 'export_readme.txt').read()
    return text



class ProjectExportQueueView(object):

    """Handle a queue of project export jobs which may take a long
    time.  So this is intended to be run in a separate thread often,
    eg. by clockserver. (An event-triggered async job would be nicer
    for the user, but since we lack infrastructure for doing things in
    the background and I found zc.async hard to install and overly
    complex ... this is probably good enough)
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.vardir = config.getConfiguration().clienthome
        self.maxwait = 30

    def __call__(self):
        count = 0
        queue = get_queue()
        starttime = time.time()
        while True:
            # Let's wait to see if anything interesting turns
            # up. This should prevent the users having to wait 0
            # to 30 seconds for clockserver to call this view.  If
            # clockserver should happen to fire again while we're
            # still exporting, that's fine... the queue ensures
            # that at most one instance of this view consumes a
            # given item from the queue.  And if the same name
            # gets stuffed in the queue more than once, the status
            # dict w/ locking should ensure that only one status
            # can exist for a given name.
            timeout = max(0, self.maxwait - (time.time() - starttime))
            try:
                name = queue.get(timeout=timeout)
            except Empty:
                break
            status = get_status(name)
            if status.running:
                logger.info('job already in progress for %r' % name)
                continue
            else:
                try:
                    status.start()
                    outfile_path = self.export(name, status)
                    status.finish(outfile_path)
                    count += 1
                except Exception, s:
                    status.fail(str(s))
                    log_exception('Failure in export of project %r:\n' 
                                  % name)
                    # XXX Is there actually any reason to keep the job around?
                    # Maybe failed jobs should be put elsewhere?

        # Something somewhere is causing ZODB to try to
        # save an instancemethod, which can't be pickled.
        # Don't know what or why, but we don't need to save
        # anything here.
        transaction.abort()
        if count:
            logger.info('Reached end of project export job queue (exported %d)'
                        % count)


    def export(self, project_id, status=None):
        """
        the async job should:

        * on any failure, delete the temp file

        * when done, notify (eg. set a PSM for the user w/ download URL)
          and release lock(s).
        """
        if status is None:
            # easier for testing so we can pass in arbitrary status.
            status = get_status(project_id)
        # We want the zip file to contain useful file names; but out
        # of general paranoia for the end user, let's remove
        # potentially evil character sequences before doing so.  (Which
        # hopefully Zope has already done.)
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
    """Does the actual work of writing content into a zipfile"""

    def __init__(self, context, request, status, context_dirname, azipfile):
        self.context = context
        self.request = request
        self.status = status
        self.context_dirname = context_dirname
        self.path = '/'.join(self.context.getPhysicalPath())
        self.zipfile = azipfile
        self.catalog = getToolByName(self.context, "portal_catalog")

    def save(self):
        sleep = lambda: time.sleep(TEST_SLEEPTIME)
        self.save_docs()
        sleep()
        self.save_wiki_pages()
        sleep()
        self.save_files()
        sleep()
        self.save_list_archives()
        sleep()
        self.save_blogs()
        sleep()

    def save_docs(self):
        self.status.progress_descr = _(u'Saving documentation')
        self.zipfile.writestr("%s/README.txt" % self.context_dirname, readme())

    def save_wiki_pages(self):
        self.status.progress_descr = _(u'Saving Wiki pages')
        for page in self.catalog(portal_type="Document", path=self.path):
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
        for afile in self.catalog(portal_type=("FileAttachment", "Image"), path=self.path):
            obj = afile.getObject()
            out_path = '%s/pages/%s' % (self.context_dirname, afile.getId)
            if isinstance(obj.data, basestring):
                self.zipfile.writestr(out_path, str(obj))
                continue
            # For large files, to avoid loading it all into memory,
            # we iterate over the data chain and write directly to disk,
            # then zip it afterward.
            data = obj.data
            temp = tempfile.NamedTemporaryFile(delete=True)
            try:
                while data is not None:
                    temp.write(data)
                    data = data.next
                self.zipfile.write(temp.name, out_path)
            finally:
                temp.close()

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


    def save_blogs(self):
        # For these we really do need to check featurelet status
        # so we know what kind of responses, if any, to expect from WP.
        featurelets = self._get_featurelets(self.context)
        if 'blog' not in featurelets:
            return
        self.status.progress_descr = _(u'Saving blog posts')
        config = getUtility(IProvideSiteConfig)

        url = '%s/%s' % (self.status.context_url,
                         '/blog/wp-admin/export.php?author=all&download=true')

        # Wordpress needs our ac cookie to authorize the download.
        headers = {'Cookie': '__ac=' + self.status.cookie}
        http = getUtility(IHTTPClient)
        http.force_exception_to_status_code = False
        http.timeout = 60
        response, content = http.request(url, 'GET', headers=headers)
        if int(response['status']) >= 400:
            msg = ("Failure connecting to wordpress at %s: %s" %
                   (url, content))
            logger.error(msg)
            self.status.fail(msg)
            return
        # Weirdly, we get a 200 response if the blog doesn't exist.
        if content[:30].lower().startswith('no blog by that name'):
            msg = ('Blog for project %r should exist but does not' 
                   % self.context.getId())
            logger.error(msg)
            self.status.fail(msg)
            return
        filename = response['content-disposition'].split('filename=')[-1]
        xml_path = '%s/blog/%s' % (self.context_dirname, filename) 
        self.zipfile.writestr(xml_path, content)

    def _get_featurelets(self, project):
        supporter = IFeatureletSupporter(project)
        all_flets = [flet for name, flet in getAdapters((supporter,), 
                                                        IFeaturelet)]
        installed_flets = [(flet.id, flet) for flet in all_flets 
                           if flet.installed]
        installed_flets = dict(installed_flets)
        return installed_flets


class ExportStatus(object):
    # This should maybe be a more proper state machine.

    QUEUED = 'queued, waiting to start'
    RUNNING = 'running'
    DONE = 'finished'
    FAILED = 'failed'
    NULL = 'no job running'

    # Max time a job can run before we call it hung. XXX will need to
    # try some very large project exports to find a good heuristic.
    maxdelta = datetime.timedelta(hours=6)

    def __init__(self, name, state=None, cookie='', context_url=''):
        self.name = name
        self.state = state or self.NULL
        self.updatetime = datetime.datetime.utcnow()
        self.starttime = None
        self.path = None
        self.filename = None
        self.progress_descr = _(u'') # More detailed human-readable state info.

        # We need to stash the requesting user's auth cookie somewhere
        # so the export can talk to wordpress.
        self.cookie = cookie
        # We also need to record the original URL early, since this can't be
        # easily reconstructed during a clockserver request.
        self.context_url = context_url

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

    def queue(self, queue):
        if self.running or self.queued:
            return
        queue.put(self.name)
        self.state = self.QUEUED
        self.updatetime = self.starttime = datetime.datetime.utcnow()
        self.progress_descr = _(u'')
        self.filename = None

    def start(self):
        self.state = self.RUNNING
        self.updatetime = self.starttime = datetime.datetime.utcnow()
        self.progress_descr = _(u'')
        self.filename = None

    def finish(self, path):
        # XXX fire an event?
        if self.failed:
            # Ok, so i guess it is a lame sort of state machine.
            return
        self.path = path
        self.filename = os.path.basename(path)
        self.state = self.DONE
        self.progress_descr = _(u'Export finished')
        self.updatetime = datetime.datetime.utcnow()

    def fail(self, msg=''):
        # XXX fire an event?
        self.state = self.FAILED
        self.progress_descr = _(u'Export failed! ${failure_msg}', {'failure_msg': msg})
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


class EnhancedSubscriberExporter(object):
    """ 
    Exports subscribers and also non-subscribed allowed senders.
    """

    def __init__(self, context):
        self.context = context

    def export_subscribers(self):
        """ Returns CSV string of subscriber data """
        # copy-pasted from listen because listen's not factored in a way
        # that i can reuse this code
        # (from listen.extras:MailingListSubscriberExporter).

        ml = IMembershipList(self.context)
        cat = getToolByName(self.context, 'portal_catalog')
        md = getToolByName(self.context, 'portal_memberdata')
        md_path = '/'.join(md.getPhysicalPath())
        file_data = []

        for email in ml.subscribers:
            memid = lookup_member_id(email, self.context)
            if memid:
                metadata = cat.getMetadataForUID('%s/%s' % (md_path, memid))
                # title gives the user's full name. It might be a good idea
                # to get the full object so we can directly access the full
                # name, but that'd be more expensive...
                title = metadata['Title']
            else: # e-mail only subscriber 
                memid = title = ""
            file_data.append(','.join([memid, title, email, 'subscribed']))

        for email, info in ml.allowed_senders_data.items():
            if info['subscriber']:
                continue
            file_data.append(','.join(['', '', email, 'allowed']))

        return "\n".join(file_data)
