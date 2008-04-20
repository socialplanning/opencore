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
from opencore.utils import get_opencore_property

from event import RemoteLoginSucceeded


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
    property (of 'lines' type) on the opencore_properties property
    sheet.
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
        remote_auth_sites = get_opencore_property('remote_auth_sites', self)
        if not remote_auth_sites:
            # no remote sites to check
            return

        if credentials.get('opencore_auth_match'):
            # SignedCookieAuth and OpenMember may set this to negate
            # remote auth attempts
            return

        username = credentials.get('login')
        root_uf = self.getPhysicalRoot().acl_users
        if root_uf.getUserById(username) is not None:
            # user exists at the Zope root, don't check remotely
            return

        mdtool = getToolByName(self, 'portal_memberdata')
        if mdtool.has_key(username):
            # member object exists on this site, probably pending
            return

        password = credentials.get('password')
        query = urlencode({'__ac_password': password})
        h = getUtility(IHTTPClient)
        for siteurl in remote_auth_sites:
            if not siteurl:
                continue
            authurl = '%s/people/%s/get-hash' % (siteurl, username)
            resp, content = h.request(authurl, 'POST', query)
            resp_code = resp.get('status')
            if resp_code == '200':
                # remote auth succeeds, we're done
                event.notify(event = RemoteLoginSucceeded(self,
                                                          username,
                                                          password,
                                                          siteurl))
                # we use same value for userid and username
                return username, username

        # all auth attempts failed
        return

InitializeClass(RemoteOpenCoreAuth)
