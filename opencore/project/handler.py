from zope.component import adapter
from zope.component import getAdapters
from zope.app.event.interfaces import IObjectModifiedEvent
from zope.app.container.interfaces import IContainerModifiedEvent
from zope.app.container.contained import IObjectRemovedEvent

from topp.featurelets.interfaces import IFeatureletSupporter, IFeaturelet

from opencore.interfaces.event import IAfterProjectAddedEvent, \
     IAfterSubProjectAddedEvent
from opencore.interfaces import IProject
from opencore import redirect

from opencore.interfaces.workflow import IWriteWorkflowPolicySupport

from Products.CMFCore.utils import getToolByName

@adapter(IAfterProjectAddedEvent)
def handle_postcreation(event):
    instance = event.project
    request = instance.REQUEST

    # add the 'project home' menu item before any others
    #@@ move to function or subscriber
    instance._initProjectHomeMenuItem()

    # add the featurelets, if any
    request.set('__initialize_project__', None)

    # Fetch the values from request and store them.
    instance.processForm(metadata=1)

    # We don't need this here. do we? DWM
    _initialize_project(instance, event.request)

    # add defaulting redirect hooks(may be overwritten by other
    # events)
    redirect.activate(instance)
    
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



@adapter(IAfterSubProjectAddedEvent)
def handle_subproject_redirection(event):
    instance = event.project
    request = event.request
    parent = event.parent 
    _handle_parent_child_association(parent, instance)


def _handle_parent_child_association(parent, child):
    child_id = child.getId()
    parent_info = redirect.get_info(parent)
    child_path = redirect.pathstr(child)
    parent_path = redirect.pathstr(parent)
    parent_info[child_id] = child_path

    child_url = parent_info.url
    if not child_url.endswith('/'):
        child_url += '/'
    child_url += child_id

    child_info = redirect.activate(child, url=child_url)
    child_info.parent = parent_path


@adapter(IProject, IObjectModifiedEvent)
def save_featurelets(obj, event=None, request=None):
    """
    IObjectModified event subscriber that installs the appropriate
    featurelets.
    """
    if IContainerModifiedEvent.providedBy(event):
        # we only care about direct edits
        return
    
    if not request:
        request = obj.REQUEST

    if event and request.get('__initialize_project__', None):
        # bail if project isn't actuated yet and we are used via an
        # IObjectModifiedEvent event
        return

    if request.get('set_flets') is None:
        # don't do anything unless we're actually coming from the
        # project edit screen
        return

    # XXX there must be a better way... :-|
    if request.get('flet_recurse_flag') is not None:
        return

    request.set('flet_recurse_flag', True)
    supporter = IFeatureletSupporter(obj)
    flets = dict(getAdapters((supporter,), IFeaturelet))

    desired = request.form.get('featurelets')
    if desired is None:
        desired = tuple()
    desired = set(desired)
    installed = set([name for name, flet in flets.items() if flet.installed])

    needed = desired.difference(installed)
    for flet_id in needed:
        supporter.installFeaturelet(flets[flet_id])

    removed = installed.difference(desired)
    for flet_id in removed:
        supporter.removeFeaturelet(flets[flet_id])

def add_redirection_hooks(container, ignore=[]):
    for obj in container.objectValues():
        if IProject.providedBy(obj) and obj.getId() not in ignore:
            redirect.activate(obj)

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
