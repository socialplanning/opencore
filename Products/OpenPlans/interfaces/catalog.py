from zope.interface import Interface

class IIndexingGhost(Interface):

    def getValue(name, default):
        """
        Returns a value for an column or index
        that an object does not have a attribute
        or method.  
        """

