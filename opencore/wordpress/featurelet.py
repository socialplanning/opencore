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
        #uri = "%/openplans-create-blog.php" % wp_uri.get()
        uri = "http://localhost:8090/openplans-create-blog.php"
        params = {}

        params['domain'] = domain = "%s.openplans.org" % obj.getId()

        auth = obj.acl_users.credentials_signed_cookie_auth
        secret = auth.secret
        sig = hmac.new(secret, domain, sha).digest()
        params['signature'] = sig = sig.encode('base64').strip()

        params['title'] = obj.Title()
        import urllib
        params = urllib.urlencode(params)

        ret = urllib.urlopen(uri, params)
        read = ret.read()
        import pdb; pdb.set_trace()
        
        return ret
