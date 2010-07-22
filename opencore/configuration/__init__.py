from pkg_resources import Requirement

OC_REQ = Requirement.parse('opencore')

# DEFAULT_ROLES should be in order from lowest to highest privilege
DEFAULT_ROLES          = ['ProjectMember', 'ProjectAdmin']

MEMBER_ROLES = ['ProjectMember']
ADMIN_ROLES = ['ProjectMember', 'ProjectAdmin']

DEFAULT_ACTIVE_MSHIP_STATES=['public', 'private']
PROJECTNAME            = "OpenPlans"

PROHIBITED_MEMBER_PREFIXES = ['openplans', 'topp', 'anon', 'admin',
                              'manager', 'webmaster', 'help', 'support']


