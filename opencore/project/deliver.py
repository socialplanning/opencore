# handlers for managing a deliverance vhoster
from OFS.interfaces import IObjectWillBeRemovedEvent, IObjectWillBeMovedEvent
from cStringIO import StringIO
from opencore.interfaces import IProject
from opencore.interfaces.event import IAfterProjectAddedEvent, IAfterSubProjectAddedEvent
from restclient import GET, POST, PUT, DELETE
from zope.app.container.interfaces import IObjectMovedEvent
from zope.app.event import IObjectCreatedEvent
from zope.app.event.interfaces import IObjectCreatedEvent
from zope.component import adapter, getUtility
from zope.interface import Interface
import simplejson

def service_url(project):
    # XXX FIXME Subprojects... vhosting baseurl comes from where now ? 
    host = 'openplans.org'
    return "http://%s.%s/.deliverance" %(project.getId(), base_host)

@adapter(IAfterProjectAddedEvent)
def init_parent_vhoster(event):
    # @@ don't know what this suppose to do
    url = service_url(event.project)
    ##

@adapter(IAfterSubProjectAddedEvent)
def init_subproject_vhoster(event):

    # XXX probably we want to post to an internal local trusted URL
    # and set the HOST header ...
    
    url = service_url(event.project)
    out = StringIO()
    simplejson.dump(out)
    #@@ httplib?
    POST("%s/remote_uris" %url, params=dict(add=out.getvalue()))


@adapter(IProject, IObjectRemovedEvent)
def remove_project(obj, event):
    pass


@adapter(IProject, IObjectWillBeMovedEvent)
def move_project(obj, event):
    pass
    
# PUT http://project.openplans.org/.deliverance/remote_uris
# content=[..., {'path': '/subproject', 'headers': {'X-Project-Name':
# 'subproject'}}]
