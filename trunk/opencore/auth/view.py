import logging

from Acquisition import aq_inner

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin
from Products.PluggableAuthService.PluggableAuthService import \
     _SWALLOWABLE_PLUGIN_EXCEPTIONS

from remoteauthplugin import RemoteOpenCoreAuth

logger = logging.getLogger('opencore')

class RemoteAuthView(BrowserView):
    """
    Handle remote authentication requests.
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def authenticate(self):
        """
        Extract username and password from request form and return
        simply 'True' or 'False'.  We iterate through the auth
        plug-ins by hand, so we can exclude OpenCore remote auth
        plug-ins, to prevent infinite auth loops when 2 sites point to
        each other.
        """
        context = aq_inner(self.context)
        pas = getToolByName(context, 'acl_users')
        plugins = pas.plugins
        try:
            authenticators = plugins.listPlugins(IAuthenticationPlugin)
        except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
            logger.info("PluggableAuthService: Plugin listing error",
                        exc_info=1)
            authenticators = tuple()
        
        form = self.request.form
        credentials = {'login': form.get('username'),
                       'password': form.get('password'),
                       }

        user_id = None
        for authenticator_id, auth in authenticators:
            if auth.meta_type == RemoteOpenCoreAuth.meta_type:
                continue
            try:
                uid_and_name = auth.authenticateCredentials(credentials)
                if uid_and_name is None or uid_and_name == (None,None):
                    continue
                user_id, name = uid_and_name
            except _SWALLOWABLE_PLUGIN_EXCEPTIONS:
                logger.info('PluggableAuthService: AuthenticationPlugin %s error',
                            authenticator_id, exc_info=1)
                continue

        if user_id:
            return 'True'
        else:
            return 'False'
