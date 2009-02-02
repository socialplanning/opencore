from Products.CMFCore.utils import getToolByName
from opencore.interfaces import IProject
from opencore.utility.interfaces import IHTTPClient
from opencore.utility.interfaces import IProvideSiteConfig
from opencore.wordpress.interfaces import IWordPressFeatureletInstalled
from plone.memoize.instance import memoizedproperty
from topp.featurelets.base import BaseFeaturelet
from topp.featurelets.interfaces import IFeaturelet
from zope.component import getUtility
from zope.interface import implements
import hmac
import logging
import sha
import urllib

log = logging.getLogger('opencore.wordpress')


class WordPressFeaturelet(BaseFeaturelet):
    """
    A featurelet that installs a WordPress blog
    """
    implements(IFeaturelet)

    id = "blog"
    title = "Blog"
    installed_marker = IWordPressFeatureletInstalled
    _required_interfaces = BaseFeaturelet._required_interfaces + (IProject,)

    _info = {'menu_items': ({'title': u'blog',
                             'description': u'WordPress',
                             'action': 'blog'
                             },
                            ),
             }

    @memoizedproperty
    def http(self):
        return getUtility(IHTTPClient)

    @property
    def wp_uri(self):
        return getUtility(IProvideSiteConfig).get('wordpress uri')

    @property
    def active(self):
        return bool(self.wp_uri)

    # @@ use a template 
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
        wp_uri = self.wp_uri
        if not wp_uri:
            # either None or empty value mean do nothing
            log.info('Failed to add WordPress blog: no WP URI set')
            return

        uri = "%s/openplans-create-blog.php" % wp_uri
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
        headers={'Content-type': 'application/x-www-form-urlencoded'}
        response, content = self.http.request(uri, 'POST', headers=headers,
                                              body=post)
        if response.status != 200:
            raise AssertionError('Failed to add blog: %s' % content)
        
        return BaseFeaturelet.deliverPackage(self, obj)

    def removePackage(self, obj, raise_error=True):
        wp_uri = self.wp_uri
        if not wp_uri:
            # either None or empty value mean do nothing
            log.info('Failed to remove WordPress blog: no WP URI set')
            return

        uri = "%s/openplans-delete-blog.php" % wp_uri
        params = {}

        params['domain'] = domain = "%s.openplans.org" % obj.getId()

        auth = obj.acl_users.credentials_signed_cookie_auth
        secret = auth.secret
        sig = hmac.new(secret, domain, sha).digest()
        params['signature'] = sig = sig.encode('base64').strip()

        params['title'] = obj.Title()
        post = urllib.urlencode(params)
        headers={'Content-type': 'application/x-www-form-urlencoded'}
        response, content = self.http.request(uri, 'POST', headers=headers,
                                              body=post)

        if response.status != 200:
            if raise_error:
                raise AssertionError('Failed to remove WordPress blog: %s' % content)
            else:
                log.info('Failed to remove WordPress blog: %s' % content)

        return BaseFeaturelet.removePackage(self, obj)
