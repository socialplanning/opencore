from urllib import urlencode

from zope import event
from zope.interface import implements
from zope.component import getUtility

from Globals import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin
from Products.CMFCore.utils import getToolByName

from opencore.utility.interfaces import IHTTPClient

from event import RemoteLoginSucceeded

TRUE = 'True'


manage_addOpenCoreRemoteAuthForm = PageTemplateFile(
        "zmi/OpenCoreRemoteAuthPluginForm.pt", globals(),
        __name__="manage_addOpenCoreRemoteAuthForm")


def manage_addOpenCoreRemoteAuth(dispatcher, id, title=None, REQUEST=None):
    """Add an OpenCore remote auth plugin to a Pluggable
    Authentication Service acl_users."""
    authplugin = RemoteOpenCoreAuth(id, title)
    dispatcher._setObject(authplugin.id, authplugin)

    if REQUEST is not None:
        query = urlencode({'manage_tabs_message':
                           'OpenCore+remote+auth+plugin+added.',
                           },
                          )
        REQUEST.RESPONSE.redirect(
                '%s/manage_workspace?%s'
                % (dispatcher.absolute_url(),
                   query)
                )


class RemoteOpenCoreAuth(BasePlugin):
    """
    Authenticates against a set of remote authentication providers.
    Fires an event upon successful authentication.  The URLs of the
    remote auth providers are retrieved from a 'remote_auth_sites'
    property (of 'lines' type) on the Portal object.
    """
    meta_type = 'OpenCore Remote Authentication'
    
    implements(IAuthenticationPlugin)

    def __init__(self, id, title=None):
        self.id = id
        self.title = title

    #
    # IAuthenticationPlugin implementation
    #
    def authenticateCredentials(self, credentials):
        """
        Iterate through the remote servers and test the credentials
        against each one in turn.
        """
        portal = getToolByName(self, 'portal_url').getPortalObject()
        remote_auth_sites = portal.getProperty('remote_auth_sites')
        if not remote_auth_sites:
            return
        
        username = credentials.get('login')
        password = credentials.get('password')
        query = urlencode({'username': username, 'password': password})
        h = getUtility(IHTTPClient)
        for siteurl in remote_auth_sites:
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
        return

InitializeClass(RemoteOpenCoreAuth)
