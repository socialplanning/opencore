from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from opencore.content.membership import OpenMembership
from opencore.content.member import OpenMember
from topp.featurelets.interfaces import IFeatureletSupporter
from topp.featurelets.interfaces import IFeaturelet
from zope.component import getAdapters


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


class AllMembersInfoXML(XMLView):
    def members(self):
        membrane_tool = getToolByName(self.context, 'membrane_tool')
        memtype = OpenMember.portal_type
        members = membrane_tool.unrestrictedSearchResults(portal_type=memtype)
        return members

class ProjectInfoXML(XMLView):
    def featurelets(self):
        supporter = IFeatureletSupporter(self.context)
        all_flets = [flet for name, flet in getAdapters((supporter,), IFeaturelet)]
        installed_flets = [flet.id for flet in all_flets if flet.installed]
        return installed_flets

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


class PlainTextView(BrowserView):
    """
    View class that sets text/plain as the content-type.
    """
    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        request.RESPONSE.setHeader('Content-Type',"text/plain")
