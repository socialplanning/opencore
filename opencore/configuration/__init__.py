from opencore.configuration.utils import product_config
import socket

# DEFAULT_ROLES should be in order from lowest to highest privilege
DEFAULT_ROLES          = ['ProjectMember', 'ProjectAdmin']
DEFAULT_ACTIVE_MSHIP_STATES=['public', 'private']
PROJECTNAME            = "OpenPlans"
COOKIE_DOMAIN = '.openplans.org'
SITE_FROM_ADDRESS = product_config('site-from-address',
                                   namespace='opencore',
                                   default='greetings@%s' % socket.getfqdn())

PROHIBITED_MEMBER_PREFIXES = ['openplans', 'topp', 'anon', 'admin',
                              'manager', 'webmaster', 'help', 'support']
