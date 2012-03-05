from opencore.export import export_utils
from opencore.interfaces import IProject
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from zope.component import adapter

@adapter(IProject, IObjectRemovedEvent)
def delete_exports(proj, event=None):
    export_utils.delete_zips(proj.getId())

