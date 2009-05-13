from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from Products.CMFCore.utils import getToolByName
from opencore.member.interfaces import IOpenMember
from opencore.member.utils import get_cleanup_queue
from zExceptions import BadRequest
from zope.app.container.interfaces import IObjectRemovedEvent
from zope.component import adapter
import datetime

@adapter(IOpenMember, IObjectRemovedEvent)
def remove_member_folder(member, event):
    """
    convenience event subscriber that removes the member's home
    folder under the people folder as well,
    and does any other needed cleanup.
    """
    
    mem_id = member.getId()
    portal = getToolByName(member, 'portal_url').getPortalObject()

    # XXX wouldn't it be better to explicitly check for the existence
    #     of the member folder rather than catching a BadRequest? -egj
    try:
        portal.people.manage_delObjects([mem_id])
    except BadRequest:
        # if the people folder was already removed first, we want to
        # fail silently
        pass

    # We also want to clean up local roles, which is too expensive to
    # do synchronously.
    queue = get_cleanup_queue(member)
    queue.put({'id': mem_id, 'deleted': datetime.datetime.now()})



def reindex_membership_project_ids(mship, event):
    """
    Event subscriber to update the project_ids index for a member,
    given a membership.
    """
    ms_tool = getToolByName(mship, 'portal_membership')
    mem = ms_tool.getMemberById(mship.id)
    return reindex_member_project_ids(mem, event)

def reindex_member_project_ids(member, event):
    """
    Event subscriber to update the project_ids index for this member.
    """
    # Make sure we have privileges to see all the projects the user's
    # a member of!  Otherwise, if this is triggered by a project
    # manager approving a join request, and the joiner is a member of
    # private projects that the project mgr cannot see, those projects
    # would be removed from the index!
    # http://trac.openplans.org/errors-openplans/ticket/36
    orig_security_mgr = getSecurityManager()
    try:
        user = getToolByName(member, 'acl_users').getUserById(member.getId())
        newSecurityManager(member, user)
        member.reindexObject(idxs=['project_ids'])
    finally:
        setSecurityManager(orig_security_mgr)


