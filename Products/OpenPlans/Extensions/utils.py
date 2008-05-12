from Products.Archetypes.Extensions.utils import install_subskin
from Products.CMFCore.utils import getToolByName
from ZODB.POSException import ConflictError
from cStringIO import StringIO
from os.path import join, abspath, dirname, basename
import ZConfig
import time

# is this used for anything (doesn't seem to be)
VOCAB_PREFIX = abspath(join(dirname(__file__), '..', 'vocabulary'))
CONF_PREFIX = abspath(join(dirname(__file__), '..', 'conf'))

def vocab_file(file): return join(VOCAB_PREFIX, file)

def conf_file(file): return join(CONF_PREFIX, file)

def register(portal, pkg):
    qi = portal.portal_quickinstaller
    if not qi.isProductInstalled(pkg):
	qi.installProduct(pkg)
	
def requires(portal, pkg):
    """Make sure that we can load and install the package into the
    site"""
    register(portal, pkg)

def optional(portal, pkg):
    try:
        register(portal, pkg)
        return True
    except ConflictError:
        raise
    except:
        return False

def parseDepends():
    schema = ZConfig.loadSchema(conf_file('depends.xml'))
    config, handler = ZConfig.loadConfig(schema,
                                         conf_file('depends.conf'))
    return config, handler

def installDepends(portal):
    config, handler = parseDepends()
    # Curry up some handlers
    def required_handler(values, portal=portal):
        for pkg in values:
            requires(portal, pkg)

    def optional_handler(values, portal=portal):
        for pkg in values:
	    optional(portal, pkg)

    handler({'required' : required_handler,
             'optional' : optional_handler,
             })


def reinstallSubskins(portal):
    out = StringIO()
    stool = getToolByName(portal, 'portal_skins')
    dels = [id for id in stool.objectIds() if id.startswith('openplans')]
    stool.manage_delObjects(ids=dels)
    install_subskin(portal, out, dict(__name__='Products.OpenPlans'))
