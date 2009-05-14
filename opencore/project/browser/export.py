from Products.CMFCore.utils import getToolByName
from opencore.browser.base import BaseView
from zipfile import ZipFile
import re
from ZPublisher.Iterators import IStreamIterator
import tempfile



class PagesExportView(BaseView):

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


    def _list_available_exports(self):
        """any zip files avail to download?
        """
        
    

    def export(self):
        """
        Return the zip file.
        """
        tempzip = self._get_exportable_data()
        self.request.RESPONSE.setHeader('Content-Type', 'application/zip')
        # Tell ZPublisher to serve this file efficiently, freeing up
        # the Zope thread immediately.  The temp file will be
        # automagically deleted when it gets garbage-collected.
        iterator = FilestreamIterator(tempzip)
        self.request.RESPONSE.setHeader('Content-Length', len(iterator))
        return iterator


class FilestreamIterator(object):

    """Wraps a file object and implements ZPublisher.Iterators.IStreamIterator,
    for efficient static file serving.

    We couldn't use the existing implementation at
    ZPublisher.Iterators.filestream_iterator, because it requires a
    filename -- but we want to use unnamed temporary files.

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
