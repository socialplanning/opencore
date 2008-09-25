"""
this is a forerunner for something that go into TeamSpaces
"""
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName 
from Products.Five.browser.TrustedExpression import getEngine
from interfaces import IProjectInfo
from opencore.interfaces import IProject, IOpenTeam
from opencore.browser.base import BaseView
from opencore.project.utils import get_featurelets
from opencore.utils import find_interface_parent
from plone.memoize import view
from zope.interface import implements

view.memoizedproperty = lambda func: property(view.memoize(func))

# assumption here is that all instances of a piv in a request will be
# for the same project. if this changes, we will memoize differently
# view.mcproperty = lambda func: property(view.memoize_contextless(func))
#
# this doesn't work when the main request is not for a project
# but there is a need for a project info view of some project 
# eg when the topnav is contextualized by http headers.

class ProjectInfoView(BaseView):
    implements(IProjectInfo)

    def __init__(self, context, request):
        self.context = context
        self._context = (context,)
        self.request = request

    def logo_url(self):
        logo = self.context.getLogo()
        if logo:
            return logo.absolute_url()
        else:
            return self.defaultProjLogoThumbURL

    @view.memoizedproperty
    def project(self):
        if IOpenTeam.providedBy(self.context):
            # get the related project
            return self.context.getProject()
        item = find_interface_parent(aq_inner(self.context),
                                     IProject) # might be None
        return item

    @property
    def inProject(self):
        inside = self.project is not None
        # XXX is this needed any more?
        self.request.set('inProject', inside)
        return inside

    @view.memoizedproperty
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

    @view.memoizedproperty
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


engine = getEngine()
evaluate = lambda text, ec: engine.compile(text)(ec)
getContext = lambda data: engine.getContext(data)


