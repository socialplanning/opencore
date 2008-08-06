# handlers for managing a deliverance vhoster
# FIXME: is anything here not cruft? I nuked the subproject stuff,
# but I don't know what any of the rest of this is for. -PW

from zope.component import queryUtility
from zope.interface import Interface, implements
from zope.schema import TextLine
from zope.component.interfaces import ComponentLookupError

class IVHosterInfo(Interface):
    """
    interface representing configuration of
    vhoster location
    """
    uri = TextLine(
        title=u"VHoster URI",
        description=u"Location of vhoster",
        required=True)
    
def vhoster_uri():
    info = queryUtility(IVHosterInfo, default=None)
    if info is not None:
        return info.uri
    else:
        raise ComponentLookupError('No virtual hosting service has been registered')


class VHosterInfo(object):
    implements(IVHosterInfo)
    def __init__(self, uri=None):
        self._uri = ''
        self._set_uri(uri)


    def _get_uri(self):
        return self._uri
    
    def _set_uri(self, uri):
        if not uri:
            self._uri = ''
            return
        
        if not '://' in uri:
            self._uri = 'http://%s' % uri
        else:
            self._uri = uri
            
        if self._uri.endswith('/'):
            self._uri += '/'

    uri = property(fset=_set_uri, fget=_get_uri) 
    
_global_vhoster_info = VHosterInfo()

def _set_vhoster_info(uri):
    _global_vhoster_info.uri = uri

def configure_vhoster_info(_context, uri):
    _context.action(
        discriminator = 'opencore.project.deliver.vhoster_info already registered',
        callable = _set_vhoster_info,
        args = (uri,)
        )
