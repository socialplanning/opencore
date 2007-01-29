from cStringIO import StringIO
from Products.Archetypes.Extensions.utils import install_subskin
from opencore.siteui import config

def install(portal):
    out = StringIO()
    install_subskin(portal, out, config.GLOBALS)
    print >> out, "Installed skin"
    return out.getvalue()    

def uninstall(portal):
    pass
