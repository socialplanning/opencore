from zope.component import adapter, getUtility
from zope.app.event.interfaces import IObjectCreatedEvent 
from zope.app.event.interfaces import IObjectModifiedEvent
from zope.app.container.interfaces import IContainerModifiedEvent

from topp.featurelets.interfaces import IFeatureletSupporter
from topp.featurelets.interfaces import IFeatureletRegistry

from opencore.interfaces.event import IAfterProjectAddedEvent, \
     IAfterSubProjectAddedEvent
from opencore.interfaces import IProject
from opencore import redirect

from Products.OpenPlans.interfaces import IWriteWorkflowPolicySupport


@adapter(IAfterProjectAddedEvent)
def handle_postcreation(event):
    instance = event.project
    request = instance.REQUEST

    # add the 'project home' menu item before any others
    #@@ move to function or subscriber
    instance._initProjectHomeMenuItem()

    # add the featurelets, if any
    #save_featurelets(instance, request=request)    
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
    

#@@ should this be own subscriber
def _initialize_project(instance, request):
    """
    This is called by the IAfterProjectAddedEvent to perform after creation
    to initialize the content within the project.
    """
    instance._createTeam()
        
    # @@ move to subscriber
    instance._createIndexPage()
    
    # Set initial security policy
    policy = request.get('workflow_policy', None)
    policy_writer = IWriteWorkflowPolicySupport(instance)
    if policy_writer is not None:
        policy_writer.setPolicy(policy)

    
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
    registry = getUtility(IFeatureletRegistry)
    supporter = IFeatureletSupporter(obj)

    desired = request.form.get('featurelets')
    if desired is None:
        desired = tuple()
    desired = set(desired)
    installed = set(supporter.getInstalledFeatureletIds())

    needed = desired.difference(installed)
    for flet_id in needed:
        flet = registry.getFeaturelet(flet_id)
        supporter.installFeaturelet(flet)

    removed = installed.difference(desired)
    for flet_id in removed:
        flet = registry.getFeaturelet(flet_id)
        supporter.removeFeaturelet(flet)

def add_redirection_hooks(container, ignore=[]):
    for obj in container.objectValues():
        if IProject.providedBy(obj) and obj.getId() not in ignore:
            redirect.activate(obj)
