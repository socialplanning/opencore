from httplib2 import Http
from opencore.utility.interfaces import IHTTPClient
from zope.interface import implements

class HTTPClient(Http):
    """
    Subclass the Http class so we can always inject Connection=close
    into the request headers, to avoid keep-alive headaches.
    """
    implements(IHTTPClient)
    
    def request(self, uri, **kw):
        """
        Inject Connection=close into the HTTP request headers.
        """
        if not kw.has_key('headers'):
            kw['headers'] = {'Connection': 'close'}
        else:
            kw['headers']['Connection'] = 'close'
        return Http.request(self, uri, **kw)
