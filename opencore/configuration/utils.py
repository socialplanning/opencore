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
