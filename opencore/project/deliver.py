# handlers for managing a deliverance vhoster

#from OFS.interfaces import IObjectWillBeRemovedEvent, IObjectWillBeMovedEvent
#from zope.app.event import IObjectCreatedEvent
#from zope.app.event.interfaces import IObjectCreatedEvent
#from zope.app.container.interfaces import IObjectMovedEvent

from opencore.interfaces import IProject
from opencore.interfaces.event import IAfterSubProjectAddedEvent
from opencore.redirect import get_redirect_url
from zope.component import adapter, getUtility, queryUtility
from urlparse import urlsplit, urljoin
import simplejson
from opencore.utility.interfaces import IHTTPClient
from zope.interface import Interface, implements
from zope.schema import TextLine, Bool
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


def project_host(project):
    url = get_redirect_url(project)
    host = ''
    if url:
        host = urlsplit(url)[1]
    return host
        

@adapter(IAfterSubProjectAddedEvent)
def handle_subproject_vhoster(event):
    parent = event.parent
    subproj = event.project

    virtual_host = project_host(parent)
    if not virtual_host:
        # don't think anything needs to happen
        return

    child_path = '/%s' % subproj.getId()

    # XXX I hate his inline REST call, this should be
    # packed up in a python API
    
    # this info tells deliverance to set the X-Openplans-Project
    # header to the subproject's id when visiting the url of the
    # subproject. 
    http = getUtility(IHTTPClient)

    uri = urljoin(vhoster_uri(), "/.deliverance/remote_uris?add")
    data = [{'path': child_path,
            'headers': {'X-Openplans-Project': subproj.getId()}}]
    headers = {'Host': virtual_host,
               'Connection': 'close'}
    
    # perform the RESTy call to deliverance 
    rc = http.request(uri,
                      method='POST',
                      body=simplejson.dumps(data),
                      headers=headers)[0]
    status = rc['status']
    status_code = int(status.split(' ')[0])

    if status_code < 200 or status_code >= 300:
        raise IOError("Unable to register project %s with virtual hosting service (status %s)" % (subproj.getId(), status))

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

#@adapter(IProject, IObjectRemovedEvent)
#def remove_project(obj, event):
#    pass
#@adapter(IProject, IObjectWillBeMovedEvent)
#def move_project(obj, event):
#    pass
    
# PUT http://project.openplans.org/.deliverance/remote_uris
# content=[..., {'path': '/subproject', 'headers': {'X-Project-Name':
# 'subproject'}}]
