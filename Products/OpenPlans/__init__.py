"""
OpenPlans
"""
__authors__ = 'Rob Miller <ra@burningman.com>'
__docformat__ = 'restructuredtext'

from AccessControl import ModuleSecurityInfo
from AccessControl import allow_module, allow_class, allow_type
from Globals import package_home
from Products.Archetypes import public as atapi
from Products.CMFCore import utils as cmf_utils
from Products.CMFCore.DirectoryView import registerDirectory
from Products.CMFCore.DirectoryView import registerFileExtension
from Products.CMFCore.FSPageTemplate import FSPageTemplate
from Products.PluggableAuthService import registerMultiPlugin
from Products.listen.permissions import AddMailingList
from opencore import configuration as config
from opencore.auth import remoteauthplugin
from opencore.bbb.module_alias import do_aliases
from opencore.nui import indexing
from opencore.utility.interfaces import IProvideSiteConfig
from permissions import initialize as initialize_permissions
from zope.component import getUtility, queryUtility, ComponentLookupError
import monkey

GLOBALS = globals()
SKINS_DIR = 'skins'

# Register Global Tools/Services/Config
# (Skins)
registerFileExtension('xsl', FSPageTemplate)
registerDirectory(SKINS_DIR, GLOBALS)

# register the remote auth PAS plugin
registerMultiPlugin(remoteauthplugin.RemoteOpenCoreAuth.meta_type)


def initialize(context):
    # Importing the content types allows for their registration
    # with the Archetypes runtime
    from content import *
    from opencore.content import *
    from opencore.listen import mailinglist

    # Register customization policy
    import policy
    policy.register(context, GLOBALS)

    from AccessControl import ModuleSecurityInfo

    msi = ModuleSecurityInfo('Products.OpenPlans.interfaces')
    msi.declarePublic('IWriteWorkflowPolicySupport')

    # Ask Archetypes to handback all the type information needed
    # to make the CMF happy.
    types = atapi.listTypes(config.PROJECTNAME)
    content_types, constructors, ftis = atapi.process_types(types,
                                                            config.PROJECTNAME)

    # XXX make this a 'z3types' data structure
    content_types = content_types + (mailinglist.OpenMailingList,)
    constructors = constructors + (mailinglist.addOpenMailingList,)
    ftis = ftis + z3ftis

    permissions = initialize_permissions()
    permissions['Open Mailing List'] = AddMailingList
    allTypes = zip(content_types, constructors)
    for atype, constructor in allTypes:
        kind = "%s: %s" % (config.PROJECTNAME,
                           getattr(atype,'archetype_name','portal_type'))
        cmf_utils.ContentInit(
            kind,
            content_types      = (atype,),
            permission         = permissions[atype.portal_type],
            extra_constructors = (constructor,),
            fti                = ftis,
            ).initialize(context)

    from opencore.auth import SignedCookieAuthHelper
    from AccessControl.Permissions import add_user_folders
    context.registerClass( SignedCookieAuthHelper.SignedCookieAuthHelper,
                           permission = add_user_folders,
                           constructors = ( SignedCookieAuthHelper.manage_addSignedCookieAuthHelperForm,
                                            SignedCookieAuthHelper.manage_addSignedCookieAuthHelper ),
                           visibility = None
                           )

    context.registerClass(remoteauthplugin.RemoteOpenCoreAuth,
                          permission = add_user_folders,
                          constructors = (remoteauthplugin.manage_addOpenCoreRemoteAuthForm,
                                          remoteauthplugin.manage_addOpenCoreRemoteAuth),
                          visibility = None
                          )

    # do all at import cataloging setup
    indexing.register_indexable_attrs()

    # bbb
    import opencore.bbb
    do_aliases()

    # note to future generations: as far as I can tell doing a component lookup here is brittle.
    # the opencore configuration should consistently be loaded before this method is run
    # but that is only because the OpenPlans product is alphabetically after the Five product and
    # so Zope loads it after loading Five; Five in turn installs opencore's configuration.
    if not queryUtility(IProvideSiteConfig):
        raise ComponentLookupError("""No utility was found to provide IProvideSiteConfig. """
                                   """You really should not start your site without one. """
                                   """If you built your stack with Fassembler, just """
                                   """`easy_install https://svn.openplans.org/svn/fassembler/configparser` """
                                   """in your opencore environment to install Fassembler's configuration provider.""")
