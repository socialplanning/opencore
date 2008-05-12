"""
config utils
"""

from App import config
from opencore.utility.interfaces import IProvideSiteConfig
from warnings import warn
from zope.component import getUtility, ComponentLookupError
import ConfigParser
import logging

logger = logging.getLogger('opencore.configuration.utils')

def product_config(variable, namespace, default=''):
    """
    get a variable from the product-config (etc/zope.conf)
    """
    try:
        cfg = config.getConfiguration().product_config.get(namespace)
    except AttributeError:
        warn("Product configuration most likely not loaded; %r not found in %r"
             % (variable, namespace))
        return default
    if cfg:
        return cfg.get(variable, default)
    return default


_parsers = {}  # Cache of ini file parsers.

def get_config(section, option, default='', inifile=None):
    """
    XXX This is here for backward compatibility only.
    You should instead be using:
    getUtility(opencore.utility.interfaces.IProvideSiteConfig).get()

    Get the value of the given option from configuration somewhere.
    Use default if option is not found.

    'section' and 'inifile' are ignored.
    """
    warn(DeprecationWarning(
        "Don't use opencore.configuration.utils.get_config(); instead use "
        "getUtility(opencore.utility.interfaces.IProvideSiteConfig).get()"))
    config = getUtility(IProvideSiteConfig)
    return config.get(option, default)

#
# This stuff should be in a config file, but we won't be using kupu
# for much longer, it's not worth the trouble
#
# XXX do we still use kupu anywhere at all? can this go away?

kupu_libraries = [
    dict(icon='string:${portal_url}/openproject_icon.png',
         id='projects',
         src='string:${portal/projects/absolute_url}/kupucollection.xml',
         title='string:Projects',
         uri='string:${portal/projects/absolute_url}'),

    dict(icon='string:${portal_url}/openproject_icon.png',
         id='current',
         src='string:${folder_url}/../kupucollection.xml',
         title='string:Current Folder',
         uri='string:${folder_url}/..'),
    
    dict(icon='string:${portal_url}/group.gif',
         id='people',
         title='string:People'),
    
    dict(icon='string:${portal_url}/kupuimages/confirm_icon.gif',
         id='myitems',
         src='string:${portal_url}/kupumyitems.xml',
         title='string:My items',
         uri='string:${portal_url}/kupumyitems.xml'),
    
    dict(icon='string:${portal_url}/kupuimages/confirm_icon.gif',
         id='recentitems',
         src='string:${portal_url}/kupurecentitems.xml',
         title='string:Recent',
         uri='string:${portal_url}/kupurecentitems.xml')]

kupu_resource_map = dict(linkable=('Document',
                              'Image',
                              'File',
                              'News Item',
                              'Event',
                              'PoiIssue',
                              'PoiResponse',
                              ),
                    mediaobject=('Image',),
                    collection=('Plone Site',
                                'Folder',
                                'OpenProject',
                                'Poitracker',
                                'Large Plone Folder'))
