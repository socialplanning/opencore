from lxml import etree

from Acquisition import aq_base
from Products.GenericSetup.interfaces import IFilesystemExporter
from Products.GenericSetup.interfaces import IFilesystemImporter
from Products.GenericSetup.tool import TOOLSET_XML
from Products.GenericSetup.utils import _resolveDottedName


def importToolset(context):

    """
    Import tools from XML file.  We don't use GenericSetup's b/c it
    sorts the tools alphabetically by name.  The sorting happens in
    the toolset registry; we let that happen, but we perform the import
    based on the order in the XML file.
    """
    site = context.getSite()
    encoding = context.getEncoding()
    logger = context.getLogger('mdtool')

    xml = context.readDataFile(TOOLSET_XML)
    if xml is None:
        logger.info('Nothing to import.')
        return

    setup_tool = context.getSetupTool()
    toolset = setup_tool.getToolsetRegistry()

    # we still let the persistent registry store the info
    toolset.parseXML(xml, encoding)

    # but we generate our own copy that retains the order from the
    # file
    ts = etree.fromstring(xml)

    existing_ids = site.objectIds()
    existing_values = site.objectValues()

    for tool_id in toolset.listForbiddenTools():

        if tool_id in existing_ids:
            site._delObject(tool_id)

    for required in ts.xpath('//required'):
        info = required.attrib
        tool_id = str(info['tool_id'])
        tool_class = _resolveDottedName(info['class'])

        existing = getattr(aq_base(site), tool_id, None)
        try:
            new_tool = tool_class()
        except TypeError:
            new_tool = tool_class(tool_id)
        else:
            try:
                new_tool._setId(tool_id)
            except: # XXX:  ImmutableId raises result of calling MessageDialog
                pass

        if existing is None:
            site._setObject(tool_id, new_tool)

        else:
            unwrapped = aq_base(existing)
            if not isinstance(unwrapped, tool_class):
                site._delObject(tool_id)
                site._setObject(tool_id, tool_class())

    logger.info('MemberData tool imported.')


def installCookieAuth(context):

    portal = context.getSite()

    uf = portal.acl_users

    login_path = 'require_login'
    logout_path = 'logged_out'
    cookie_name = '__ac'

    from Products.CMFCore.utils import getToolByName

    crumbler = getToolByName(portal, 'cookie_authentication', None)

    if crumbler is not None:
        login_path = crumbler.auto_login_page
        logout_path = crumbler.logout_page
        cookie_name = crumbler.auth_cookie
        
    found = uf.objectIds(['Signed Cookie Auth Helper'])
    if not found:
        openplans = uf.manage_addProduct['OpenPlans']
        openplans.manage_addSignedCookieAuthHelper('credentials_signed_cookie_auth',
                                                   cookie_name=cookie_name)

    from Products.PlonePAS.Extensions.Install import activatePluginInterfaces
    import sys
    activatePluginInterfaces(portal, 'credentials_signed_cookie_auth', sys.stdout)

    signed_cookie_auth = uf._getOb('credentials_signed_cookie_auth')
    if 'login_form' in signed_cookie_auth.objectIds():
        signed_cookie_auth.manage_delObjects(ids=['login_form'])
    signed_cookie_auth.cookie_name = cookie_name
    signed_cookie_auth.login_path = login_path

    old_cookie_auth = uf._getOb('credentials_cookie_auth', None)
    if old_cookie_auth is not None:
        old_cookie_auth.manage_activateInterfaces([])

    from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
    plugins = uf._getOb('plugins', None)
    if plugins is not None:
        plugins.movePluginsUp(IChallengePlugin,
                              ['credentials_signed_cookie_auth'],)


# override the default PAS handlers since those assume the setup tool
# is inside the PAS instance
def exportPAS(context):
    IFilesystemExporter(context.getSite().acl_users).export(context,
                                                            'PAS',
                                                            True)

def importPAS(context):
    if context.isDirectory('PAS'):
        import pdb;pdb.set_trace()
        IFilesystemImporter(context.getSite().acl_users).import_(context,
                                                                 'PAS',
                                                                 True)
