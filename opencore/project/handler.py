""" post creation handlers """
from opencore.interfaces.event import IAfterProjectAddedEvent, IAfterSubProjectAddedEvent
from zope.component import adapter

@adapter(IAfterProjectAddedEvent)
def handle_postcreation(event):
    instance = event.project

    # add the 'project home' menu item before any others
    instance._initProjectHomeMenuItem()

    # Fetch the values from request and store them.
    instance.processForm()

    # We don't need this here
    instance._initializeProject(event.request)

    # ugh... roster might have been created by an event before a
    # team was associated (in _initializeProject), need to fix up
    roster_id = instance.objectIds(spec='OpenRoster')
    if roster_id:
        roster = instance._getOb(roster_id[0])
        if not roster.getTeams():
            roster.setTeams(instance.getTeams())


@adapter(IAfterSubProjectAddedEvent)
def handle_subproject_redirection(event):
    instance = event.project
    request = event.request
    parent = event.parent 
    _handle_parent_child_association(parent, instance)


def _handle_parent_child_association(parent, child):
    child_id = child.getId()
    parent_info = redirect.get_info(parent)
    parent_path = redirect.pathstr(child)
    parent_info[child_id] = parent_path
    child_url = "%s/%s" %(parent_info.url, child_id) 
    redirect.activate(child, url=child_url, parent=parent_path)
