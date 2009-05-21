from opencore.configuration.utils import product_config
from pkg_resources import Requirement
from zope.component import queryUtility

OC_REQ = Requirement.parse('opencore')

# DEFAULT_ROLES should be in order from lowest to highest privilege
DEFAULT_ROLES          = ['ProjectMember', 'ProjectAdmin']
DEFAULT_ACTIVE_MSHIP_STATES=['public', 'private']
PROJECTNAME            = "OpenPlans"

class __useless(object):
    # this is here just so we can create a property

    _cookie_domain = None

    @classmethod
    def cookie_domain(kls):
        # Bootstrap this on first usage to avoid using the component
        # architecture during package load.
        # XXX Is this actually used anywhere??
        if kls._cookie_domain is None:
            from opencore.utility.interfaces import IProvideSiteConfig
            config = queryUtility(IProvideSiteConfig)
            kls._cookie_domain = config.get('cookie_domain')
        return kls._cookie_domain

COOKIE_DOMAIN = __useless.cookie_domain

PROHIBITED_MEMBER_PREFIXES = ['openplans', 'topp', 'anon', 'admin',
                              'manager', 'webmaster', 'help', 'support']


