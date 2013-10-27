from App import config
from Products.CMFCore.utils import getToolByName
from Products.listen.interfaces import IMailingListMessageExport
from Products.listen.interfaces import IMailingListSubscriberExport
from Products.listen.interfaces import IMembershipList
from Products.listen.lib.common import lookup_member_id
from Queue import Queue, Empty
from libopencore.auth import parse_cookie
from lxml.html import fromstring, tostring
from opencore.i18n import _, translate
from opencore.interfaces import IHomePage
from opencore.interfaces.workflow import IReadWorkflowPolicySupport
from opencore.nui.wiki import bzrbackend
from opencore.listen.interfaces import ISyncWithProjectMembership
from opencore.listen.utils import mlist_type_to_workflow
from opencore.listen.utils import mlist_archive_policy
from opencore.utility.interfaces import IEmailSender
from opencore.utility.interfaces import IHTTPClient
from opencore.utility.interfaces import IProvideSiteConfig
from pkg_resources import resource_stream, resource_filename
from topp.featurelets.interfaces import IFeatureletSupporter
from topp.featurelets.supporter import IFeaturelet
from zipfile import ZipFile
from zope.app.component.hooks import getSite
from zope.app.component.hooks import setSite
from zope.component import getAdapter
from zope.component import getAdapters
from zope.component import getUtility

from zope.app.annotation.interfaces import IAnnotations 
from opencore.member.interfaces import IHandleMemberWorkflow

import StringIO
import datetime
import logging
import os
import re
import shutil
import simplejson as json
import tempfile
import tempita
import threading
import time
import traceback
import transaction

TEMP_PREFIX='temp_project_export'

# For interactive testing, it's useful to be able to slow things down
# and watch progress.
TEST_SLEEPTIME=0

logger = logging.getLogger('opencore.export')

# valid characters are letters, digits, underscores, and hyphens
badchars = re.compile(r'[^\w\-]+')

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

def get_status(name, cookie='', context_url='', features=None):
    """ Get or create an ExportStatus instance for the given identifier."""
    _status_lock.acquire()
    try:
        if name not in _status_dict:
            _status_dict[name] = ExportStatus(name, context_url=context_url,
                                              cookie=cookie)
        if features is not None and len(features) > 0:
            _status_dict[name].features = features
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
    text = resource_stream('opencore.export', 'export_readme.txt').read()
    return text

def css():
    text = resource_stream('opencore.export', 'css.txt').read()
    return text

def mlist_conf(ctx):
    tmplfile = resource_filename('opencore.export', 'export_list_conf.ini.tmpl')
    tmpl = tempita.Template.from_filename(tmplfile)
    return tmpl.substitute(**ctx)

def project_metadata(ctx):
    tmplfile = resource_filename('opencore.export', 'export_project_metadata.ini.tmpl')
    tmpl = tempita.Template.from_filename(tmplfile)
    return tmpl.substitute(**ctx)

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
        self.notify = True

    def __call__(self, maxwait=None):
        count = 0
        names = []
        queue = get_queue()
        starttime = time.time()
        
        # We allow the remote caller to specify
        # a maxwait parameter to override the
        # default, but it has to be a valid int
        # smaller than the default. We don't want
        # to allow requests to last arbitrarily
        # long, even if they're made by admins.
        if maxwait is not None:
            try:
                maxwait = int(maxwait)
            except TypeError:
                maxwait = self.maxwait
            if maxwait > self.maxwait:
                maxwait = self.maxwait
        else:
            maxwait = self.maxwait

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
            timeout = max(0, maxwait - (time.time() - starttime))
            try:
                name = queue.get(timeout=timeout)
            except Empty:
                break
            status = get_status(name)
            if status.running:
                logger.info('job already in progress for %r' % name)
                continue

            try:
                # we want a fresh transaction
                # in case content has changed
                # since the beginning of this thread
                transaction.commit()
                status.start()
                outfile_path = self.export(name, status)
                status.finish(outfile_path)
                transaction.commit()
                count += 1
                names.append(name)
            except Exception, s:
                status.fail(str(s))
                log_exception(
                    'Failure in export of project %r:\n' 
                    % name)
                # XXX Is there actually any reason to keep the job around?
                # Maybe failed jobs should be put elsewhere?
            if self.notify:
                self.send_mail(status)

        # Something somewhere is causing ZODB to try to
        # save an instancemethod, which can't be pickled.
        # Don't know what or why, but we don't need to save
        # anything here.
        #import pdb; pdb.set_trace()
        #transaction.abort()
        if count:
            logger.info('Reached end of project export job queue (exported %d)'
                        % count)
        return names

    def send_mail(self, status):
        site = getSite()

        try:
            project = site.restrictedTraverse('projects/%s' % status.name)
        except:
            log_exception("Couldn't access project %s -- not sending email" % status.name)
            return

        try:
            username = status.user()
        except:
            log_exception("Couldn't parse cookie %s to extract username -- not sending email" % status.cookie)
            return

        mto = [username]

        if status.succeeded:
            msg_subs = {'project': project.Title(),
                        'url': '%s/export/%s' % (
                    status.context_url,
                    status.filename),
                        'portal_title': site.Title()
                        }

            msg = _(u'Your export of project "${project}" has finished.\n\nYou can download it by clicking this link: ${url}\n\nCheers,\nThe ${portal_title} Team')
            subject = _(u'Project export complete')
        elif status.failed:
            msg_subs = {'project': project.Title(),
                        'portal_title': site.Title()
                        }

            msg = _(u'Your export of project "${project}" has failed because of an internal error. We apologize for the inconvenience.\n\nThe site administration has been notified of the problem and we will let you know as soon as the error has been fixed.\nThe ${portal_title} Team')
            subject = _(u'Project export failed, sorry!')
            mto.append(site.getProperty('email_from_address'))
        else:
            return

        IEmailSender(site).sendMail(
            mto=mto,
            msg=msg,
            subject=subject,
            **msg_subs)

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
        logger.info("Exporting %s ..." % self.path)
        sleep = lambda: time.sleep(TEST_SLEEPTIME)
        logger.info("1. Saving docs")
        self.save_docs()
        sleep()
        logger.info("2. Saving wiki pages")
        if self.status.include_wiki_pages():
            self.save_wiki_pages()
        sleep()
        logger.info("3. Saving files")
        if self.status.include_wiki_pages():
            self.save_files()
        sleep()
        logger.info("4. Saving mailing lists")
        if self.status.include_mailing_lists():
            self.save_list_archives()
        sleep()
        logger.info("5. Saving blogs")
        if self.status.include_blog():
            self.save_blogs()
        sleep()
        logger.info("6. Saving wiki history")
        if self.status.include_wiki_history():
            self.save_wiki_history()
        sleep()
        logger.info("7. Saving project team and metadata")
        self.save_project_metadata()
        logger.info("done with %s" % self.path)

    def save_docs(self):
        self.status.progress_descr = _(u'Saving documentation')
        self.zipfile.writestr("%s/README.txt" % self.context_dirname, readme())

    def save_project_metadata(self):
        self.status.progress_descr = _(u'Saving project team and metadata')
        project = self.context

        reader = IReadWorkflowPolicySupport(self.context)
        policy = reader.getCurrentPolicyId()

        hpcontext = IHomePage(self.context)
        homepage = hpcontext.home_page

        featurelets = self._get_featurelets(project)

        project_info = {
            'id': project.getId(),
            'title': project.Title(),
            'created_on': str(project.created()),
            'modified_on': str(project.modified()),
            'creator': project.Creator(),
            'location': project.getLocation(),

            'description': project.Description(),
            'security_policy': policy,
            'homepage': homepage,
            'featurelets': ','.join(featurelets),

            }

        logo_info = {
            'logo_filename': None,
            'logo_created_on': None,
            'logo_modified_on': None,
            'logo_creator': None,
            'logo_zippath': None,
            }
        logo = project.getLogo()
        if logo is not None:
            logo_info['logo_filename'] = logo.filename
            logo_info['logo_created_on'] = str(logo.created())
            logo_info['logo_modified_on'] = str(logo.modified())
            logo_info['logo_creator'] = logo.Creator()

            import mimetypes
            extension = mimetypes.guess_extension(logo.content_type) or ''
            logo_info['logo_zippath'] = "%s/project/logo%s" % (self.context_dirname, extension)

        project_info.update(logo_info)

        conf_path = '%s/project/settings.ini' % self.context_dirname
        self.zipfile.writestr(conf_path, project_metadata(project_info))
        self.zipfile.writestr(
            "%s/project/description.txt" % self.context_dirname,
            project_info['description'])

        if logo is not None:
            logo_filepath = logo_info['logo_zippath']
            if isinstance(logo.data, basestring):
                self.zipfile.writestr(logo_filepath, logo.data)
            else:
                assert isinstance(logo.data.data, basestring)
                self.zipfile.writestr(logo_filepath, logo.data.data)

        view = project.restrictedTraverse("@@manage-team")

        team_data = {}

        team_data['members'] = [
            {'user_id': mship['getId'],
             'role': mship['role_value'],
             'timestamp': str(mship['active_since']),
             'listed': mship['listed'],
             } for mship in view.active_mships]
        team_data['join_requests'] = [
            {'user_id': mship.getId,
             'timestamp': str(mship.lastWorkflowTransitionDate),
             } for mship in view.pending_requests]
        team_data['member_invites'] = [
            {'user_id': mship.getId,
             'timestamp': str(mship.lastWorkflowTransitionDate),
             } for mship in view.pending_invitations]
        team_data['email_invites'] = [
            {'email': mship['address'],
             'timestamp': str(mship['timestamp']),
             } for mship in view.pending_email_invites]

        team_data['unconfirmed_join_requests'] = []
        mems = app.openplans.portal_memberdata
        for mem in mems.keys():
            mreqs = IAnnotations(mems[mem]).get(
                "opencore.member.pending_requests", {})
            if self.context.getId() in mreqs:
                team_data['unconfirmed_join_requests'].append({
                        'user_id': mem, 'message': mreqs[self.context.getId()]})

            from pprint import pprint
            pprint(team_data)

        self.zipfile.writestr('%s/project/team.json' % self.context_dirname,
                              json.dumps(team_data, indent=2))

    def save_wiki_history(self):
        self.status.progress_descr = _(u'Saving wiki history')
        project = self.context
        tempdir = tempfile.mkdtemp()

        tmpdbdir = os.path.join(tempdir, "tmpdbs")
        repodir = os.path.join(tempdir, "bzr_repos")
        checkoutdir = os.path.join(tempdir, "bzr_checkouts")

        try:
            converter = bzrbackend.WikiConverter(
                project, tmpdbdir, repodir, checkoutdir)

            clonedir, filename_map = converter.convert()
            root_len = len(os.path.abspath(clonedir))

            for root, dirs, files in os.walk(clonedir):
                relative_root = os.path.abspath(root)[root_len:].strip(os.sep)
                archive_root = os.path.join(
                    self.context_dirname, 'wiki_history',
                    relative_root)
                for f in files:
                    fullpath = os.path.join(root, f)
                    archive_name = os.path.join(archive_root, f)
                    self.zipfile.write(fullpath, archive_name)
            self.zipfile.writestr(os.path.join(self.context_dirname,
                                               "wiki_history_filenames.json"),
                                  json.dumps(filename_map))
        finally:
            shutil.rmtree(tempdir)

    def save_wiki_pages(self):
        self.status.progress_descr = _(u'Saving Wiki pages')
        for page in self.catalog(portal_type="Document", path=self.path):
            try:
                page = page.getObject()
            except AttributeError:
                logger.warn("Failed to export page at %s; catalog ghost??"
                            % page.getPhysicalPath)

            text = page.getText().decode("utf-8")
            
            # out of general paranoia for the end user, let's remove
            # potentially evil character sequences before archiving.
            # (Which hopefully Zope has already done.)
            page_id = page.getId()
            page_id = badchars.sub('_', page_id)

            # Wrap the HTML in an <html> node with head and body;
            # add the page title in a <h1> like in the wiki;
            # link to the exported css file we'll add to the 
            # zipfile below; and add all the essential class 
            # markup for the CSS rules.
            title = page.Title().decode("utf-8")

            text = (u'<body class="oc-wiki">\n<h1>%s</h1>\n' % title +
                    u'<div class="oc-wiki-content">\n'
                    + text + u"\n</div>\n</body>")

            # We want to rewrite links to other wiki pages,
            # so that the wiki will form a valid web after 
            # we export it and save the HTML files with 
            # a .html extension.  The goal is to let this
            # export be uploaded to any web server and be
            # a valid site with no broken links.
            # But we need to NOT extend the link url with
            # the .html extension if the link is to a file!

            # The page content may contain resolved wicked links
            # which are resolved based on the current request URL.
            # So if this code's clockserver job isn't careful
            # about using VirtualHostMonster-aware paths,
            # it could end up with ugly localhost:port URLs.
            # So we'll swap out URLs in the content that look like
            # current-request-based URLs, and replace them
            # with URLs based on the user's request that initiated
            # the export -- which is handily stored on the status object.
            # This won't cover ALL cases in theory (e.g. if there is 
            # a generated link to a resource outside the project) 
            # but it will cover the most likely cases, namely
            # wicked links.  Why else would there be generated URLs 
            # in content, anyway?
            # To be really careful, the clockserver jobs should
            # be configured to use VHM-aware urls like
            #   method /VirtualHostBase/http/www.coactivate.org:80/++skin++avata/openplans/VirtualHostRoot/manage_project_export_queue
            # (for coactivate.org)
            base = self.status.context_url
            request_base = self.context.absolute_url()
            body = fromstring(text)
            def link_repl_func(url):
                if url.startswith(request_base):
                    url = url.replace(request_base, base)
                if not url.startswith(base):
                    return url
                path = url.replace(base, '')
                physical_path = '/'.join((self.path.rstrip('/'), path.lstrip('/')))
                brains = self.catalog(path=physical_path, 
                                      portal_type=("Document", "FileAttachment", "Image"))
                matching_brains = [brain for brain in brains
                                   if brain.getPath() == physical_path]
                if not len(matching_brains):
                    # It's a link to some kind of resource
                    # that isn't part of the static wiki dump,
                    # so just leave it as whatever it is.
                    # Like maybe it's a mailing list post.
                    # So just leave it as a link to the site.
                    return url
                brain = matching_brains[0]
                type = brain.portal_type
                if type == "Document":
                    # It's a page, so we'll add the extension
                    return path.lstrip('/') + '.html'
                else:
                    # It's an attachment, so we don't add the extension
                    return path.lstrip('/')

            # In the live wiki, the base href is the wikipage itself.
            # Which is a bit lame, but we need to keep that here
            # to ensure links don't break.  We're going to rewrite
            # all links to be absolute anyway, and then re-relativize
            # links to intra-wiki content with the project root itself
            # as the base href.
            base_href = base.rstrip('/') + '/' + page.getId() + '/'
            body.rewrite_links(link_repl_func, base_href=base_href)
            text = tostring(body)

            text = ('<html><head>\n' +
                    '<link rel="stylesheet" href="style.css" type="text/css" media="all" />' +
                    '</head>' + text + '</html>')

            self.zipfile.writestr("%s/pages/%s.html" % (
                    self.context_dirname, page_id), text)

        # Export a minimal stylesheet to preserve users' page layouts
        # and essential theming.  Right now this is just ".pullquote" and "pre"
        # but it might grow based on user feedback.
        # The wiki page .html exports all link to this in their <head> styles.
        self.zipfile.writestr("%s/pages/style.css" % self.context_dirname,
                              css())

        # We'll also add a root index.html with a meta-refresh redirect
        # to the project-home.html page, but only if they don't have
        # a page called "index" yet.
        index_path = "%s/index" % self.path.rstrip('/')
        if len(list(self.catalog(portal_type="Document", path=index_path))) > 0:
            return
        self.zipfile.writestr("%s/pages/index.html" % self.context_dirname,
                              """<html><head><meta http-equiv="refresh" content="0;url=project-home.html" /></head><body></body></html>""")
            
    def save_files(self):
        self.status.progress_descr = _(u'Saving images and file attachments')
        file_metadata = {}
        for afile in self.catalog(portal_type=("FileAttachment", "Image"), path=self.path):
            obj = afile.getObject()

            # Files should be saved in a directory named for
            # the page they're attached to, so links work.
            relative_path = afile.getPath()[len(self.path):].lstrip('/')
            out_path = '%s/pages/%s' % (self.context_dirname, relative_path)

            assert out_path not in file_metadata, out_path
            metadata = {
                'creator': obj.Creator(),
                'creation_date': str(obj.creation_date),
                'title': obj.Title(),
                }
            file_metadata[out_path] = metadata

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

        self.zipfile.writestr("%s/attachments.json" % self.context_dirname, 
                              json.dumps(file_metadata))

    def save_list_archives(self):
        self.status.progress_descr = _(u'Saving mailing lists')
        try:
            listfol = self.context['lists']
        except KeyError:
            logger.error("No lists subfolder on %s" % self.context.getId())
            return

        real_site = getSite()
        for mlistid, mlist in listfol.objectItems(): # XXX filter more?
            logger.info("exporting %s" % mlistid)
            setSite(mlist)  # Needed to get the export adapter.
            mlistid = badchars.sub('_', mlistid)
            # Cargo-culted from listen/browser/import_export.py
            em = getAdapter(mlist, IMailingListMessageExport, name='mbox')
            # Nooo don't do it all in memory, we have seen some huge archives.
            #file_data = em.export_messages() or ''
            #self.zipfile.writestr('%s/lists/%s.mbox' % (self.context_dirname, mlistid),
            #                     file_data)
            tmpfd, tmpname = em.export_messages_to_tempfile()
            self.zipfile.write(tmpname,
                               '%s/lists/%s/archive.mbox' % (self.context_dirname, mlistid))
            os.unlink(tmpname)
            del(tmpfd)

            # Now the list subscribers.
            logger.info("exporting subscribers.csv for %s" % mlistid)
            es = getAdapter(mlist, IMailingListSubscriberExport, name='csv')
            file_data = es.export_subscribers(
                include_allowed_senders=True) or ''
            csv_path = '%s/lists/%s/subscribers.csv' % (self.context_dirname, mlistid)
            self.zipfile.writestr(csv_path, file_data)

            # Now the metadata and preferences.
            logger.info("exporting settings.ini for %s" % mlistid)
            list_info = {
                'id': mlist.getId(),
                'type': mlist_type_to_workflow(mlist),
                'mailto': mlist.mailto,
                'managers': mlist.managers,
                'archive_setting': mlist_archive_policy(mlist),
                'title': mlist.Title(),
                'description': mlist.Description(),
                'creation_date': str(mlist.created()),
                'modification_date': str(mlist.modified()),
                'creator': mlist.Creator(),
                'sync_with_project': ISyncWithProjectMembership.providedBy(mlist),
                'context': self.context.getId(),
                'private_archives': mlist.private_archives,
                }
            conf_path = '%s/lists/%s/settings.ini' % (self.context_dirname, mlistid)
            self.zipfile.writestr(conf_path, mlist_conf(list_info))

            setSite(real_site)
            logger.info("finished %s" % mlistid)

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

        if response.get('content-location').count('/login?came_from'):
            msg = 'Could not authenticate to blog %s' % url
            logger.error(msg)
            self.status.fail(msg)
            return
        if not 'content-disposition' in response:
            msg = "No content-disposition in response?"
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

        self.features = ["wikipages", "mailinglists", "blog", "wikihistory"]

    def include_wiki_pages(self):
        return "wikipages" in self.features
    def include_wiki_history(self):
        return "wikihistory" in self.features
    def include_mailing_lists(self):
        return "mailinglists" in self.features
    def include_blog(self):
        return "blog" in self.features

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

    def user(self):
        username, __ = parse_cookie(self.cookie)
        return username

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

def getzips(project_id, vardir=None):
    path = getpath(project_id, vardir)
    zips = [f for f in os.listdir(path) if 
            (f.endswith('.zip') and
             not f.startswith(TEMP_PREFIX))]
    zips.sort(reverse=True)
    return zips

def delete_zips(project_id, vardir=None):
    zips = getzips(project_id, vardir)
    path = getpath(project_id, vardir)
    for f in zips:
        os.unlink(os.path.join(path, f))
