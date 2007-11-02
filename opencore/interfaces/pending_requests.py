from zope.interface import Interface

class IPendingRequests(Interface):
    """
    Interface for a local utility that tracks project membership
    requests for a user which should not be activated yet (eg
    for unconfirmed users)
    """
    def getRequests():
        """
        Returns a tuple of project ids of pending membership requests.
        """
    
    def addRequest():
        """
        Adds a pending membership request.
        """

    def removeRequest():
        """
        Removes a pending membership request.
        """

    def removeAllRequestsForUser():
        """
        Removes all pending membership requests associated with a user.
        """
    
