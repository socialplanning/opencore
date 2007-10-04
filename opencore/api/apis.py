from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from opencore.content.membership import OpenMembership

class XMLView(BrowserView):
    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        request.RESPONSE.setHeader('Content-Type',"application/xml")


class MemberInfoXML(XMLView):
    # XXX memoize?
    def member(self):
        mem_folder = self.context
        pm = getToolByName(mem_folder, "portal_membership")
        mem_id = mem_folder.getId()
        return pm.getMemberById(mem_id)


# ugh.
class AllMembersInfoXML(XMLView):
    def members(self):
        membrane_tool = getToolByName(self.context, 'membrane_tool')
        members = membrane_tool.unrestrictedSearchResults()
        return members


class ProjectMembershipXML(XMLView):

    # XXX should probably memoize this?
    def team(self):
        teams = self.context.getTeams()
        assert len(teams) == 1
        return teams[0]

    # XXX memoize this too, i imagine
    # XXX merge with opencore.nui.ManageTeamView.project.active_mships
    def members(self):
        team = self.team()
        team_path = '/'.join(team.getPhysicalPath())
        cat = getToolByName(self.context, "portal_catalog")
        mem_ids = team.getActiveMemberIds()
        brains = cat(portal_type=OpenMembership.portal_type,
                     path=team_path,
                     id=mem_ids)
        return brains
