from urllib import urlencode

from zope import event
from zope.interface import implements
from zope.component import getUtility

from Products.PluggableAuthService.interfaces import IAuthenticationPlugin
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin

from opencore.utility.interfaces import IHTTPClient

from event import RemoteLoginSucceeded
from config_tmp import REMOTE_AUTH_SITES

TRUE = 'True'

class RemoteOpenCoreAuth(BasePlugin):
    """
    Authenticates against a set of remote authentication providers.
    Fires an event upon successful authentication.
    """
    
    implements(IAuthenticationPlugin)

    #
    # IAuthenticationPlugin implementation
    #
    def authenticateCredentials(credentials):
        """
        Iterate through the remote servers and test the credentials
        against each one in turn.
        """
        username = credentials.get('login')
        password = credentials.get('password')
        query = urlencode({'username': username, 'password': password})
        h = getUtility(IHTTPClient)
        for siteurl in REMOTE_AUTH_SITES:
            authurl = '%s/authenticate-credentials?%s' % (siteurl, query)
            resp, content = h.request(authurl, 'GET')
            if content == TRUE:
                # SUCCESS
                event.notify(event = RemoteLoginSucceeded(self,
                                                          username,
                                                          password,
                                                          siteurl))
                # we use same value for userid and username
                return username, username

        # all remote auth attempts failed
        return None
