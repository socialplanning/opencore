import hmac, sha
from memojito import memoizedproperty

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
        uri = "%/openplans_create_blog.php" % wp_uri.get()
        params = {}

        params['domain'] = domain = "%s.openplans.org" % obj.getId()

        auth = obj.acl_users.credentials_signed_cookie_auth
        secret = auth.secret
        params['signature'] = hmac.new(secret, domain, sha).digest()

        params['title'] = obj.getTitle()
        body = "&".join(["%s=%s" % (i, params[i]) for i in params])
        return self.http.request(uri, method="POST", body=body)
