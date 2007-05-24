"""
this is a forerunner for something that go into TeamSpaces
"""
from zope.interface import implements

from Products.CMFCore.utils import getToolByName 
from Products.Five import BrowserView
from Products.Five.browser.TrustedExpression import getEngine
from Products.OpenPlans.interfaces import IProject, IOpenTeam
from memojito import memoizedproperty
from interfaces import IProjectInfo


class ProjectInfoView(BrowserView):
    implements(IProjectInfo)

    def __init__(self, context, request):
        self.context = context
        self._context = (context,)
        self.request = request

    @memoizedproperty
    def project(self):
        if IOpenTeam.providedBy(self.context):
            # get the related project
            return self.context.getProject()
        # probably wrap this in an adapter
        chain = self._context[0].aq_chain
        for item in chain:
            if IProject.providedBy(item):
                return item

    @memoizedproperty
    def inProject(self):
        inside = self.project is not None
        # XXX is this needed any more?
        self.request.set('inProject', inside)
        return inside

    @memoizedproperty
    def projectMembership(self):
        pm = getToolByName(self.context, 'portal_membership')
        if pm.isAnonymousUser():
            return False
        
        member = pm.getAuthenticatedMember()
        for team in self.project.getTeams():
            mship = team.getMembershipByMemberId(member.getId(),
                                                 active_only=True)
            if mship is not None:
                return mship
            
        return False

    @memoizedproperty
    def featurelets(self):
        flets = []
        if self.project is not None:
            supporter = IFeatureletSupporter(self.project)
            flet_ids = supporter.getInstalledFeatureletIds()
            getfletdesc = supporter.getFeatureletDescriptor
            flets = [{'name': id,
                      'url' : getfletdesc(id)['content'][0]['id']}
                     for id in flet_ids]
        return flets


engine = getEngine()
evaluate = lambda text, ec: engine.compile(text)(ec)
getContext = lambda data: engine.getContext(data)
