"""
this is a forerunner for something that go into TeamSpaces
"""
from zope.interface import implements

from Products.CMFCore.utils import getToolByName 
from Products.Five import BrowserView
from Products.Five.browser.TrustedExpression import getEngine
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
    def navname(self):
      return self.inProject and self.project.Title()

    @memoizedproperty
    def fullname(self):
      return self.inProject and self.project.getFull_name()

    @memoizedproperty
    def url(self):
        """Returns the url of the project"""
        return self.project and self.project.absolute_url()

    def featurelets(self):
      """Returns a dict of featurelets installed for this project.
      Keys are the featurelet names, values are their urls."""
      # TODO
      return {}

    @memoizedproperty
    def homePageHTML(self):
        """Returns the 'cooked body' of the project's homepage."""
        if self.inProject:
            homepage = self.project.getDefaultPage()
            homepage = self.project.unrestrictedTraverse(homepage)
            return homepage.CookedBody()

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
