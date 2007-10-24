from zope.interface import Interface
from zope.interface import implements

class IRemoteLoginSucceeded(Interface):
    """
    Authentication against a remote OpenPlans server was successful.
    """

class RemoteLoginSucceeded(object):
    implements(IRemoteLoginSucceeded)

    def __init__(self, context, username, password, siteurl):
        self.context = context
        self.username = username
        self.password = password
        self.siteurl = siteurl
