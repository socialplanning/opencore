from Products.CMFCore.utils import getToolByName
from opencore.member.interfaces import IOpenMember
from zExceptions import BadRequest
from zope.app.container.interfaces import IObjectRemovedEvent
from zope.component import adapter

@adapter(IOpenMember, IObjectRemovedEvent)
def remove_member_folder(member, event):
    """convenience event subscriber that removes the member's home
       folder under the people folder as well"""
    
    id = member.getId()
    portal = getToolByName(member, 'portal_url').getPortalObject()
    try:
        portal.people.manage_delObjects([id])
    except BadRequest:
        # if the people folder was already removed first, we want to
        # fail silently
        pass

def reindex_member_project_ids(mship, event):
    ms = getToolByName(mship, 'portal_membership')
    mem = ms.getMemberById(mship.id)
    mem.reindexObject(idxs=['project_ids'])
