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

@adapter(IAfterProjectAddedEvent)
def handle_postcreation(event):
    instance = event.project
    request = instance.REQUEST

    # Fetch the values from request and store them.
    instance.processForm(metadata=1)

    # We don't need this here. do we? DWM
    _initialize_project(instance, event.request)

    # ugh... roster might have been created by an event before a
    # team was associated (in _initializeProject), need to fix up
    roster_id = instance.objectIds(spec='OpenRoster')
    if roster_id:
        roster = instance._getOb(roster_id[0])
        if not roster.getTeams():
            roster.setTeams(instance.getTeams())

    # we need to remove the Owner role which is assigned to the
    # member who created the project; otherwise the creator will
    # have all administrative privileges even after he leaves
    # the project or is demoted to member.
    owners = instance.users_with_local_role("Owner")
    instance.manage_delLocalRoles(owners)
    # @@ why don't i need to reindex allowed roles and users?

#@@ should this be own subscriber
def _initialize_project(instance, request):
    """
    This is called by the IAfterProjectAddedEvent to perform after creation
    to initialize the content within the project.
    """
    instance._createTeam()

    # Set initial security policy
    policy = request.get('workflow_policy', None)
    policy_writer = IWriteWorkflowPolicySupport(instance)
    if policy_writer is not None:
        policy_writer.setPolicy(policy)

    # @@ move to subscriber
    instance._createIndexPage()


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
