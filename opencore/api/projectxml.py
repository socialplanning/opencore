from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from opencore.content.membership import OpenMembership

class ProjectMembershipXML(BrowserView):

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        response = request.RESPONSE
        response.setHeader('Content-Type',"application/xml")

    def team(self):
        teams = self.context.getTeams()
        assert len(teams) == 1
        return teams[0]

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
