from zope.interface import Interface
from zope.interface import implements
from zope.interface import directlyProvidedBy
from zope.component import adapts

from Products.CMFCore.utils import getToolByName

from Products.OpenPlans.interfaces import IProject
from opencore.listen.interfaces import IOpenMailingList
from opencore.featurelets.interfaces import IListenFeatureletInstalled

class ITellYouAboutContent(Interface):
    """
    An adapter to query for information about a particular
    content type within a certain context.
    """

    def recent():
        """
        Return the mailing lists with recently posted messages,
        sorted by date of most recent activity.
        """

class QueryMailingLists(object):
    """
    The idea is that this is a particular implementation of ITellYouAboutContent
    specifically for Open Mailing Lists within a project; another implementation
    would provide data about Open Documents, and another would provide data
    about wordpress blogs, and another about tasklists.

    There's a big problem, though, which is that I can't actually figure out
    how to convey that information.  I don't think I'm supposed to adapt
    IOpenMailingList, because at the time of getting the adapter I'll only
    have a project, not a mailing list; is there a mailing list container 
    object I'm supposed to adapt?  Or am I supposed to somehow pass in the
    IOpenMailingList interface itself?  Or perhaps the ListenFeaturelet 
    should contain the answer somehow?  (I say should because I'm pretty sure
    it currently does not)

    Or is this idea incoherent?
    """
    implements(ITellYouAboutContent)
    adapts(IProject)
    
    def __init__(self, project):
        # XXX i think we should be using the featurelet installation marker
        #     here -- might as well use what we have
        # XXX but should i be getting it directly or should i be getting
        #     ListenFeaturelet.installed_marker?
        if IListenFeatureletInstalled not in directlyProvidedBy(project):
            # XXX i dunno what to do here, but we should do something
            #     so i'll raise a string exception for now! okay!
            raise "No mailing lists available"

        self.project = project

        # XXX the ListenFeaturelet knows where all mailing lists
        #     will reside, so i should probably use that instead
        #     of just project_path
        self.search_path = '/'.join(project.getPhysicalPath())
        self.catalog = getToolByName(project, "portal_catalog")

        # XXX i could grab this from a OpenMailingList object
        #     and am sure i should rather than hardcoding this
        #     text, but i don't know where i would get such an
        #     object. see general statement of problem in the
        #     class's docstring.
        self.portal_type = "Open Mailing List" 

    def recent(self, n=10):
        brains = self.catalog(portal_type=self.portal_type,
                              path=self.search_path,
                              sort_on="lastModifiedDate",
                              sort_order="descending",
                              sort_limit=n)
        return brains
