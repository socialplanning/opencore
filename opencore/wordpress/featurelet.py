import hmac, sha
import urllib
from memojito import memoizedproperty

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from topp.featurelets.base import BaseFeaturelet
from opencore.wordpress.interfaces import \
    IWordPressFeatureletInstalled, IWordPressContainer
from opencore.wordpress import uri as wp_uri

class WordPressFeaturelet(BaseFeaturelet):
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

    #creation_command = ZopeTwoPageTemplateFile("create_blog.pt")

    def creation_command(self, signature, domain, title, members):
        return """<blog>
 <signature>
   %s
 </signature>
 <domain>
   %s
 </domain>
 <title>
   %s
 </title>
 %s
</blog>
""" % (signature, domain, title, members)

    def deliverPackage(self, obj):
        uri = "%s/openplans-create-blog.php" % wp_uri.get()
        params = {}

        params['domain'] = domain = "%s.openplans.org" % obj.getId()

        auth = obj.acl_users.credentials_signed_cookie_auth
        secret = auth.secret
        sig = hmac.new(secret, domain, sha).digest()
        params['signature'] = sig = sig.encode('base64').strip()

        params['title'] = obj.Title()

        if obj.getTeams():
            params['members'] = obj.restrictedTraverse("memberships.xml")()
        else: # no team has been set up yet, so fake it
            pm = getToolByName(obj, "portal_membership")
            id_ = pm.getAuthenticatedMember().getId()
            params['members'] = "<members><member><id>%s</id><role>ProjectAdmin</role></member></members>" % id_

        #post = self.creation_command(**params)
        post = urllib.urlencode(params)

        response = urllib.urlopen(uri, post)
        response = response.read()
        if "Created blog ID" not in response:
            raise AssertionError("Failed to create blog. %s" % response)
        
        return BaseFeaturelet.deliverPackage(self, obj)
