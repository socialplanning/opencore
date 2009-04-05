from lxml.html.clean import Cleaner
import urlparse

class MonkeyCleaner(Cleaner):
    """
    This override departs from the default lxml.html.clean:Cleaner
    implementation by statefully storing the set of elements that
    were removed during processing so that we can report this
    information back to the user.
    
    The set of elements removed is stored in the `tags_removed`
    attribute on the object.
    
    See http://trac.openplans.org/openplans/ticket/2793
    """
    def __init__(self, *args, **kw):
        self.tags_removed = []
        Cleaner.__init__(self, *args, **kw)

    def allow_embedded_url(self, el, url):
        allowed = Cleaner.allow_embedded_url(self, el, url)
        if not allowed:
            scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
            netloc = netloc.lower().split(':', 1)[0]
            self.tags_removed.append((el, netloc))
        return allowed
