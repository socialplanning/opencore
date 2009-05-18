from ZPublisher.Iterators import IStreamIterator
from opencore.browser.base import BaseView
from opencore.project.browser import export_utils
from Acquisition import Explicit
from zExceptions import Forbidden
import os
import simplejson as json

class ProjectExportView(BaseView):

    """
    Export a project's wiki pages as a zipfile of html.

    This needs to happen asynchronously.
    the export page can report status; when done,
    show a download link.
    - if js available, do this nice and ajaxy
    - if noscript, maybe do a meta refresh? (is noscript legal in <head>?)

    Another async job could periodically check for old completed
    exports and delete them, if we care. (eg. greater than 30 days)

    """

    # I suppose I could have written this with oc-behaviors and
    # octopolite, but a) i still don't really grok octopolite, and b)
    # chris P. had already nicely written the jquery code for me so I
    # might as well use that. - PW

    vardir = None  # so we can patch it for testing.

    def available_exports(self):
        """any zip files avail to download?
        """
        path = export_utils.getpath(self.context.getId(), self.vardir)
        zips = [f for f in os.listdir(path) if f.endswith('zip')]
        return sorted(zips, reverse=True)

    def available_exports_json(self):
        """yup, it's json"""
        return json.dumps(self.available_exports)

    def current_status(self):
        queue = export_utils.get_queue(self.context)
        try:
            return queue[self.context.getId()]
        except KeyError:
            # set up a null status, not in the queue.
            return export_utils.ExportStatus(self.context.getId())

    def current_status_json(self):
        """Current export status, as json. """
        status = self.current_status()
        return status.json()

    def do_export(self):
        """Fire off an export, asynchronously."""
        # XXX I tried to use @post_only, but it mysteriously
        # causes this method not to be available via URL.
        # maybe cuz it messes up the function's name?? shrug.
        if self.request.environ['REQUEST_METHOD'] != 'POST':
            raise Forbidden('GET is not allowed here')
        queue = export_utils.get_queue(self.context)
        status = export_utils.ExportStatus(self.context.getId())
        queue[status.name] = status
        status.state = status.QUEUED
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
        iterator = FilestreamIterator(open(thezip))
        self.request.RESPONSE.setHeader('Content-Length', len(iterator))
        # Needs to be aq-wrapped to satisfy the security machinery.
        return iterator.__of__(self)


class FilestreamIterator(Explicit):

    """Wraps a file object and implements ZPublisher.Iterators.IStreamIterator,
    for efficient static file serving.

    We couldn't use the existing implementation at
    ZPublisher.Iterators.filestream_iterator, because it requires a
    filename -- but we want to use unnamed temporary files.
    XXX actually we don't use temp files anymore.
    XXX Maybe we can just use the ZPublisher one after all?

    I had hoped it would be possible to just do:

       zope.interface.classImplements(file, IStreamIterator)

    ... somewhere, and then just return the file object and have it
    Just Work.

    But that doesn't work because A) IStreamIterator is an old-style
    Zope 2 interface, which you can't use with builtin types (aargh),
    and B) even if I hack Zope to use a zope 3 interface there, it
    starts to work and then somehow my temporary file gets closed
    before ZServer is done with it, which makes ZServer die.
    """

    __implements__ = (IStreamIterator,)


    def __init__(self, afile, streamsize=1<<16):
        self.__inner = afile
        self.streamsize = streamsize

    def next(self):
        data = self.__inner.read(self.streamsize)
        if not data:
            self.__inner.close()
            raise StopIteration
        return data

    def __len__(self):
        # Why don't files implement this already, anyway?
        cur_pos = self.__inner.tell()
        self.__inner.seek(0, 2)
        size = self.__inner.tell()
        self.__inner.seek(cur_pos, 0)
        return size

