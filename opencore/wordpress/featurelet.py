import hmac, sha
import urllib
from memojito import memoizedproperty

from topp.featurelets.base import BaseFeaturelet
from opencore.featurelets.satellite import SatelliteFeaturelet
from opencore.wordpress.interfaces import \
    IWordPressFeatureletInstalled, IWordPressContainer
from opencore.wordpress import uri as wp_uri

class WordPressFeaturelet(SatelliteFeaturelet):
    """
    A featurelet that installs a WordPress blog
    """

    id = "blog"
    title = "WordPress"
    installed_marker = IWordPressFeatureletInstalled

    _info = {'menu_items': ({'title': u'blog',
                             'description': u'WordPress',
                             'action': 'blog'
                             },
                            ),
             }

    def deliverPackage(self, obj):
        uri = "%s/openplans-create-blog.php" % wp_uri.get()
        params = {}

        params['domain'] = domain = "%s.openplans.org" % obj.getId()

        auth = obj.acl_users.credentials_signed_cookie_auth
        secret = auth.secret
        sig = hmac.new(secret, domain, sha).digest()
        params['signature'] = sig = sig.encode('base64').strip()

        params['title'] = obj.Title()
        params = urllib.urlencode(params)

        response = urllib.urlopen(uri, params)
        response = response.read()
        if "Created blog ID" not in response:
            raise AssertionError("Failed to create blog. %s" % response)
        
        return BaseFeaturelet.deliverPackage(self, obj)
