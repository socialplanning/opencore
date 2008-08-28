from zope.component import adapter
from zope.component import getAdapters
from zope.app.event.interfaces import IObjectModifiedEvent
from zope.app.container.interfaces import IContainerModifiedEvent
from zope.app.container.contained import IObjectRemovedEvent

from topp.featurelets.interfaces import IFeatureletSupporter, IFeaturelet

from opencore.interfaces.event import IAfterProjectAddedEvent
from opencore.interfaces import IProject

from opencore.interfaces.workflow import IWriteWorkflowPolicySupport

from Products.CMFCore.utils import getToolByName


# @@TODO: this could be asynchronous
@adapter(IProject, IObjectRemovedEvent)
def unindex_project(project, event):
    """
    Make sure a project object is unindexed when it's deleted, since
    manage_delObjects on the projects folder doesn't.
    """
    cat = getToolByName(project, 'portal_catalog')
    path = '/'.join(project.getPhysicalPath())
    if cat._catalog.hasuid(path):
        cat.unindexObject(project)
