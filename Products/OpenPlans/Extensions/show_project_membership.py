from Products.CMFCore.utils import getToolByName
from Products.Archetypes.utils import OrderedDict

def show_project_membership(self):
    portal = getToolByName('portal_url').getPortalObject()
    result_map = OrderedDict()
    pfolder = portal.projects
    proj_ids = list(pfolder.objectIds())
    proj_ids.sort()
    for proj_id in proj_ids:
        proj_map = result_map[proj_id] = OrderedDict()
        proj = pfolder._getOb(proj_id)
        mem_ids = proj.projectMemberIds()
        mem_ids.sort()
        for mem_id in mem_ids:
            proj_map[mem_id] = proj.get_local_roles_for_userid(mem_id)

    return proj_map
