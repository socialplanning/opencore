from zope.interface import Interface

class IIndexingGhost(Interface):

    def getValue(name, default):
        """
        Returns a value for an column or index
        that an object does not have a attribute
        or method.  
        """

class ILastWorkflowActor(Interface):

    def getValue():
        """
        Returns the 'actor' from the last workflow transition.  Used
        for membership objects to efficiently determine who requested
        the team membership.
        """

class ILastModifiedAuthorId(Interface):
    """string id for last author to modify a piece of content"""
