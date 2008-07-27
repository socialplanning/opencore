from zope.interface import Interface, Attribute
from zope.viewlet.interfaces import IViewletManager

class IProjectInfo(Interface):
    """
    A project centric form of basic teamspace info. 
    """
    inProject = Attribute("whether or not a piece of content is within a project")
    project = Attribute("the project for a contained piece of content")
    isProjectMember = Attribute("current user is member of project")
    projectMembership = Attribute("a current user's membership object")


class IProjectListingAllow(Interface):
    
    def getProjects():
        """
        return project in a path in alphabetical order
        """

class ISummaryFeeds(IViewletManager):
    """Feeds for the summary page"""

