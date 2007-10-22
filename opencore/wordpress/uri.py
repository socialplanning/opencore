"""
utility, directive and helper functions for locating the active
wordpress instance
"""
from opencore.wordpress.interfaces import IWordPressInfo
from zope.interface import implements
from zope.component import getUtility
from App import config

class WordpressURI(object):
    implements(IWordPressInfo)
    def __init__(self, uri=None, external_uri=None):
        self.uri = uri
        self.external_uri = external_uri

_wp_info = WordpressURI()

def set_wp_info(uri, external_uri=None):
    _wp_info.uri=uri
    _wp_info.external_uri = external_uri

def configure_wp_info(_context, uri, external_uri=None):
    _context.action(
        # if more than one WP_info is registered, will raise conflict
        # warning. can be overridden after configuration
        discriminator = 'opencore.wordpress.wp_info already registered',
        callable = set_wp_info,
        args = (uri, external_uri,)
        )

def get():
    cfg = config.getConfiguration().product_config.get('opencore.wordpress')
    fallback = getUtility(IWordPressInfo).uri
    if cfg:
        return cfg.get('uri', fallback)
    return fallback

def get_external_uri():
    cfg = config.getConfiguration().product_config.get('opencore.wordpress')
    fallback = getUtility(IWordPressInfo).external_uri
    if cfg:
        return cfg.get('external_uri', fallback)
    return fallback
