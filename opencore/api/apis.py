from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from opencore.content.membership import OpenMembership
from opencore.content.member import OpenMember

class XMLView(BrowserView):
    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        request.RESPONSE.setHeader('Content-Type',"application/xml")

    def exists(self):
        """
        Returns an empty string; browser:page tags can specify this
        attribute as a view on content to support existence checks; if
        the content exists response is 200, if not response is 404.
        """
        return ''

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
        memtype = OpenMember.portal_type
        members = membrane_tool.unrestrictedSearchResults(portal_type=memtype)
        return members
    def home_page_for(self, mem):
        #XXX ideally, we would get the home page dynamically for each member
        # but that requires a member object now, which would make things slow
        # we could add a new piece of metadata that contains this,
        # but it's not necessary just yet
        mem_id = mem.getId
        return '%s/%s/%s-home' % (self.context.absolute_url(),
                                  mem_id,
                                  mem_id,
                                  )
                                  

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
