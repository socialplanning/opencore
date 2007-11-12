from opencore.configuration.utils import product_config
#import socket


# DEFAULT_ROLES should be in order from lowest to highest privilege
DEFAULT_ROLES          = ['ProjectMember', 'ProjectAdmin']
DEFAULT_ACTIVE_MSHIP_STATES=['public', 'private']
PROJECTNAME            = "OpenPlans"
COOKIE_DOMAIN = '.openplans.org'

PROHIBITED_MEMBER_PREFIXES = ['openplans', 'topp', 'anon', 'admin',
                              'manager', 'webmaster', 'help', 'support']

# BBB
import sys
import opencore.interfaces.member
import opencore.browser
sys.modules['opencore.siteui'] = opencore.browser
sys.modules['opencore.siteui.interfaces'] = opencore.interfaces.member
del sys
