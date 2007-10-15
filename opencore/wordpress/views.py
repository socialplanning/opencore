import hmac
import sha
import urllib

from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView

from opencore.content.membership import OpenMembership

from opencore.wordpress import uri as wp_uri

class SyncUsersView(BrowserView):
    def sync(self):
        base_uri = wp_uri.get()
        uri = "%s/openplans-sync-users.php" % base_uri
        params = {}

        # XXX should be moved out somewhere.. wordpress.utils? or is it more general?
        auth = self.context.acl_users.credentials_signed_cookie_auth
        secret = auth.secret
        sig = hmac.new(secret, "admin", sha).digest() # XXX use real user, don't fake it (but wait for WP to be ok with that)
        params['signature'] = sig = sig.encode('base64').strip()

        params = urllib.urlencode(params)
        response = urllib.urlopen(uri, params)

        response = response.read()
        return "%s\nOK, now have a blast!" % response
        
