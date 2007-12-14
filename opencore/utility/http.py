from httplib2 import Http
from httplib2 import DEFAULT_MAX_REDIRECTS
from opencore.utility.interfaces import IHTTPClient
from zope.interface import implements

class HTTPClient(Http):
    """
    Subclass the Http class so we can always inject Connection=close
    into the request headers, to avoid keep-alive headaches.
    """
    implements(IHTTPClient)
    
    def request(self, uri, method="GET", body=None, headers={},
                redirections=DEFAULT_MAX_REDIRECTS, connection_type=None):
        """
        Inject Connection=close into the HTTP request headers.
        """
        if not headers.has_key('Connection'):
            headers['Connection'] = 'close'
        return Http.request(self, uri, method, body, headers, redirections,
                            connection_type)
