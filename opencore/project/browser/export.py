from ZPublisher.Iterators import filestream_iterator
from opencore.browser.base import BaseView
from opencore.project.browser import export_utils
from Acquisition import Explicit
from zExceptions import Forbidden
import os
import simplejson as json


class ProjectExportView(BaseView):

    """
    Export a project's content pages as a zipfile of html.

    This is done asynchronously (by a clockserver job that hits
    another view).  the export page reports status; when done, it
    shows a download link.

    To do: another async job to periodically check for old completed
    exports and delete them. (eg. greater than 30 days)

    """

    # I suppose I could have written this with oc-behaviors and
    # octopolite, but a) i still don't really grok octopolite, and b)
    # chris P. had already nicely written the jquery code for me so I
    # might as well use that. If anyone wants to rewrite it, feel
    # free. - PW

    vardir = None  # so we can patch it for testing.

    def available_exports(self):
        """any zip files avail to download?
        """
        path = export_utils.getpath(self.context.getId(), self.vardir)
        zips = [f for f in os.listdir(path) if 
                (f.endswith('.zip') and not f.startswith(export_utils.TEMP_PREFIX))]
        zips.sort(reverse=True)
        # don't want to pile up zip files forever...
        # in lieu of a UI or a sensible policy, we'll just keep the last 5
        zips, excess_zips = zips[:5], zips[5:]
        for f in excess_zips:
            os.unlink(os.path.join(path, f))
        return zips

    def available_exports_json(self):
        """json representation"""
        return json.dumps(self.available_exports())

    def current_status(self):
        cookie = self.request.cookies.get('__ac', '')
        name = self.context.getId()
        url = self.context.absolute_url()
        status = export_utils.get_status(name, context_url=url, cookie=cookie)
        return status

    def current_status_json(self):
        """Current export status, as json. """
        status = self.current_status()
        return status.json()

    def do_export(self):
        """Fire off an export, asynchronously."""
        if self.request.environ['REQUEST_METHOD'] != 'POST':
            # I tried to use @post_only, but it mysteriously
            # causes this method not to be available via URL.
            # maybe cuz it messes up the function's name?? shrug.
            raise Forbidden('only POST is allowed for this view')
        queue = export_utils.get_queue()
        status = self.current_status()
        # XXX should check state here.
        status.queue(queue)
        return status.json()
 
    def __getitem__(self, name):
        """
        Return a zip file.
        """
        zips = self.available_exports()
        path = export_utils.getpath(self.context.getId(), self.vardir)
        try:
            index = zips.index(name)
        except ValueError:
            # want a 404 here.
            raise KeyError(name)
        thezip = os.path.join(path, zips[index])
        self.request.RESPONSE.setHeader('Content-Type', 'application/zip')
        # Tell ZPublisher to serve this file efficiently, freeing up
        # the Zope thread immediately.
        iterator = FilestreamIterator(thezip)
        self.request.RESPONSE.setHeader('Content-Length', len(iterator))
        # Needs to be aq-wrapped to satisfy the security machinery.
        return iterator.__of__(self)

    def readme(self):
        return export_utils.readme()


class FilestreamIterator(filestream_iterator, Explicit):

    """Wraps a file object and implements ZPublisher.Iterators.IStreamIterator,
    for efficient static file serving.
    Also supports acquisition to make security happy.
    """
    def __iter__(self):
        # Standard python iterator protocol.
        # Not really needed by IStreamIterator, but makes testing easier.
        return self

    def __repr__(self):
        return '<open FilestreamIterator %r at %s>' % (self.name, id(self))
