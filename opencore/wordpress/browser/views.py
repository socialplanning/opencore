import hmac
import sha
import urllib
from httplib2 import Http
from opencore.utils import get_opencore_property

from Products.CMFCore.utils import getToolByName
from opencore.browser.base import BaseView

from opencore.content.membership import OpenMembership

class SyncUsersView(BaseView):
    def sync(self):
        base_uri = get_opencore_property('wordpress_uri')
        uri = "%s/openplans-do-sync.php" % base_uri
        params = {}

        # XXX should be moved out somewhere.. wordpress.utils? or is it more general?
        auth = self.context.acl_users.credentials_signed_cookie_auth
        secret = auth.secret
        sig = hmac.new(secret, "admin", sha).digest() # XXX use real user, don't fake it (but wait for WP to be ok with that)
        params['signature'] = sig = sig.encode('base64').strip()

        all_member_view = self.context.people.restrictedTraverse('all.xml')
        all_member_data = all_member_view()
        params['members'] = all_member_data

        params = urllib.urlencode(params)

        http = Http()
        headers={'Content-type': 'application/x-www-form-urlencoded'}
        response, content = http.request(uri, 'POST', headers=headers,
                                         body=params)
        
        self.request.RESPONSE.setHeader('Content-Type',"text/html")
        return content
