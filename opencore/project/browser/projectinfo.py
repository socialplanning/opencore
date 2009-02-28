"""
this is a forerunner for something that go into TeamSpaces
"""
from zope.interface import implements

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName 
from interfaces import IProjectInfo
from opencore.interfaces import IProject, IOpenTeam
from opencore.nui.contexthijack import HeaderHijackable
from opencore.project.utils import get_featurelets
from opencore.utils import interface_in_aq_chain
from plone.memoize import instance
from plone.memoize import view


class ProjectInfo(object):
    implements(IProjectInfo)

    def __init__(self, context):
        self.context = context

    def logo_url(self):
        logo = self.context.getLogo()
        if logo:
            return logo.absolute_url()
        else:
            return self.defaultProjLogoThumbURL

    @instance.memoizedproperty
    def project(self):
        context = aq_inner(self.context)
        if IOpenTeam.providedBy(self.context):
            # get the related project
            return aq_inner(context.getProject())
        # probably wrap this in an adapter
        return interface_in_aq_chain(context, IProject)

    @property
    def inProject(self):
        inside = self.project is not None
        # XXX is this needed any more?
        self.request.set('inProject', inside)
        return inside

    @instance.memoizedproperty
    def projectMembership(self):
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return False
        
        member = pm.getAuthenticatedMember()
        for team in self.project.getTeams():
            mship = team.getMembershipByMemberId(member.getId(),
                                                 active_only=True)
            if mship is not None:
                return True
            
        return False

    @instance.memoizedproperty
    def projectAdmin(self):
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return False
        
        member = pm.getAuthenticatedMember()
        for team in self.project.getTeams():
            role = team.getHighestTeamRoleForMember(member.getId())
            if role == 'ProjectAdmin':
                return True
        return False

    @view.memoizedproperty
    def featurelets(self):
        flets = []
        if self.project is not None:
            flets = get_featurelets(self.project)
        return flets

# assumption here is that all instances of a piv in a request will be
# for the same project. if this changes, we will memoize differently
#
# this doesn't work when the main request is not for a project
# but there is a need for a project info view of some project 
# eg when the topnav is contextualized by http headers.

class ProjectInfoView(ProjectInfo, HeaderHijackable):
    def __init__(self, context, request):
        self.context = context
        self._context = (context,)
        self.request = request

    @instance.memoizedproperty
    def project(self):
        proj_in_chain = super(ProjectInfoView, self).project
        if proj_in_chain is not None:
            return proj_in_chain
        # Use the headerhijack stuff.
        maybe_project = self.context
        if IProject.providedBy(maybe_project):
            return maybe_project
        else:
            return None

    def person_folder_from_headers(self):
        # We don't ever want to treat the person as a project!
        return None


