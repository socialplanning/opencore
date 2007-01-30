"""
this is a forerunner for something that go into TeamSpaces
"""
from zope.interface import implements

from Products.CMFCore.utils import getToolByName 
from Products.Five import BrowserView
from Products.Five.browser.TrustedExpression import getEngine
from Products.wicked.lib.normalize import titleToNormalizedId as normalize
from Products.OpenPlans.interfaces import IProject
from memojito import memoizedproperty
from interfaces import IProjectInfo


class ProjectInfoView(BrowserView):
    implements(IProjectInfo)
    def __init__(self, context, request):
        self._context = (context,)
        self.request = request

    @property
    def context(self):
        return self._context[0]

    @memoizedproperty
    def project(self):
        # probably wrap this in an adapter
        chain = self.context.aq_chain
        project = None
        for item in chain:
            if IProject.providedBy(item):
                project = item
                break
        return project

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

engine = getEngine()
evaluate = lambda text, ec: engine.compile(text)(ec)
getContext = lambda data: engine.getContext(data)
