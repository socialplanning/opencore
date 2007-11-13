from Products.CMFCore.utils import getToolByName
from Products.OpenPlans import config
from Products.OpenPlans.content.team import OpenTeam
from Products.OpenPlans.permissions import DEFAULT_PFOLDER_PERMISSIONS_DATA
from Products.OpenPlans.permissions import PLACEFUL_PERMISSIONS_DATA
from Products.OpenPlans.workflows import MEMBERSHIP_PLACEFUL_POLICIES
from Products.OpenPlans.workflows import PLACEFUL_POLICIES
from Products.PlonePAS.Extensions.Install import activatePluginInterfaces
from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
from Products.remember.utils import getAdderUtility
from StringIO import StringIO
from opencore.configuration import OC_REQ as OPENCORE
from opencore.content.member import OpenMember
from opencore.content.membership import OpenMembership
from opencore.interfaces import IAddProject
from opencore.interfaces import IAmANewsFolder
from opencore.interfaces import IAmAPeopleFolder
from opencore.interfaces.membership import IEmailInvites
from opencore.interfaces.message import ITransientMessage
from opencore.member.transient_messages import TransientMessage
from opencore.project.browser.email_invites import EmailInvites
from utils import kupu_libraries
from utils import kupu_resource_map
from zope.app.component.hooks import setSite
from zope.component import queryUtility
from zope.interface import alsoProvides
import os
import pkg_resources
import socket


Z_DEPS = ('PlacelessTranslationService', 'Five', 'membrane', 'remember',
          'GenericSetup', 'CMFPlone', 'ManagableIndex', 'QueueCatalog',
          'txtfilter')

MEM_DEPS = ('membrane', 'remember')

DEPS = ('wicked', 'TeamSpace', 'CMFPlacefulWorkflow', 'RichDocument',
        'listen', 'CMFDiffTool', 'CMFEditions')

def setuphandler(fn):
    """
    Decorator that turns QI functions into setuphandlers.
    """
    def execute_handler(context):
        stepname = fn.__name__
        handlers = context.readDataFile('setuphandlers.txt')
        if handlers is None or stepname not in handlers:
            return
        portal = context.getSite()
        out = StringIO()
        fn(portal, out)
        logger = context.getLogger('OpenCore setuphandlers')
        logger.info(out.getvalue())
    execute_handler.orig = fn
    return execute_handler

@setuphandler
def install_mem_dependencies(portal, out):
    print >> out, ('Installing membrane and remember')
    qi = getToolByName(portal, 'portal_quickinstaller')
    for dep in MEM_DEPS:
        print >> out, '--> installing: %s' % dep
        qi.installProduct(dep)

@setuphandler
def install_dependencies(portal, out):
    print >> out, ('Installing dependency products')
    qi = getToolByName(portal, 'portal_quickinstaller')
    for dep in DEPS:
        print >> out, '--> installing: %s' % dep
        qi.installProduct(dep)

@setuphandler
def install_team_placeful_workflow_policies(portal, out):
    print >> out, 'Installing team placeful workflow policies'

    # Install default policy
    pwf_tool = getToolByName(portal, 'portal_placeful_workflow')
    teams = getToolByName(portal, 'portal_teams')
    wf_config = pwf_tool.getWorkflowPolicyConfig(teams)
    if wf_config is None:
        print >> out, 'Setting default team security policy to Open'
        teams.manage_addProduct['CMFPlacefulWorkflow'].manage_addWorkflowPolicyConfig()
        wf_config = pwf_tool.getWorkflowPolicyConfig(teams)
        wf_config.setPolicyBelow(policy='mship_open_policy')
        wf_tool = getToolByName(teams, 'portal_workflow')
        wf_tool.updateRoleMappings()

@setuphandler
def installWorkflowPolicies(portal, out):
    pwf_tool = getToolByName(portal, 'portal_placeful_workflow')
    pols = PLACEFUL_POLICIES
    # also initialize the membership placeful policies
    pols.update(MEMBERSHIP_PLACEFUL_POLICIES)
    existing_pols = pwf_tool.objectIds()
    default_chains = getDefaultChains(portal)
    for pol_id, pol in pols.items():
        if pol_id not in existing_pols:
            print >> out, '-> Adding workflow policy %s' % pol_id
            pwf_tool.manage_addWorkflowPolicy(pol_id)
            new_pol = getattr(pwf_tool, pol_id)
            new_pol.setTitle(pol['title'])
            new_pol.setDescription(pol['description'])
            new_pol.setDefaultChain(pol['default'])
            # first we explicitly copy the default chains
            for chain in default_chains:
                new_pol.setChain(chain['id'],chain['chain'])
            # then we override them w/ any custom settings we want
            for p_type, chain in pol['types'].items():
                new_pol.setChain(p_type, chain)

def getDefaultChains(portal):
    pwf = getToolByName(portal, 'portal_workflow')
    cbt = pwf._chains_by_type
    ti = pwf._listTypeInfo()
    types_info = []
    for t in ti:
        id = t.getId()
        title = t.Title()
        if title == id:
            title = None
        if cbt is not None and cbt.has_key(id):
            chain = ', '.join(cbt[id])
        else:
            chain = '(Default)'
        types_info.append({'id': id,
                            'title': title,
                            'chain': chain})
    return types_info

def setPermissions(obj, perm_data, out):
    """ apply the specified permission settings to obj """
    for roles, perms in perm_data:
        for perm in perms:
            try:
                obj.manage_permission(perm, roles=roles)
                print >> out, '-> Specifying "%s" permission access for %s' \
                      % (perm, obj.getId())
            except ValueError:
                # permission doesn't exist... that's okay
                pass

@setuphandler
def securityTweaks(portal, out):
    """ tweak site-wide security settings """
    print >> out, 'Modifying site security settings'
    for obj_path, obj_perms in PLACEFUL_PERMISSIONS_DATA.items():
        obj = portal.unrestrictedTraverse(obj_path)
        setPermissions(obj, obj_perms, out)

@setuphandler
def setupVersioning(portal, out):
    versioned_types = ('Document', 'Event', 'News Item', 'Link', 'File', 'Image')
    ttool = getToolByName(portal, 'portal_types')
    version_tool = getToolByName(portal, 'portal_repository', None)
    diff_tool = getToolByName(portal, 'portal_diff', None)
    if version_tool is not None:
        version_tool.setVersionableContentTypes(versioned_types)
        action = version_tool.getActionObject('object/Versions')
        if action is not None:
            action.edit(title='History')

    for p_type in versioned_types:
        if version_tool is not None:
            version_tool.addPolicyForContentType(p_type, 'at_edit_autoversion')
            try:
                version_tool.addPolicyForContentType(p_type, 'version_on_revert')
            except AssertionError:
                version_tool.addPolicyForContentType(p_type, 'version_on_rollback')
        if diff_tool is not None:
            diff_tool.manage_addDiffField(p_type, 'none', 'Compound Diff for AT types')
        print >> out, 'Enabled versioning for %s'%p_type
    if diff_tool is not None:
        ttool.ChangeSet.global_allow = False

@setuphandler
def setMemberType(portal, out):
    mtype = 'OpenMember'
    print >> out, 'Specifying %s as default member type' % mtype
    adder = getAdderUtility(portal)
    adder.default_member_type = mtype

    # have to REset the MDC allowed types, since remember's install
    # undid what we have specified in the GenericSetup profile
    ttool = getToolByName(portal, 'portal_types')
    mdc_fti = ttool._getOb('MemberDataContainer')
    mdc_fti.manage_changeProperties(allowed_content_types=('Member',
                                                           'OpenMember',
                                                           ))

@setuphandler
def setTeamType(portal, out):
    tmtool = getToolByName(portal, 'portal_teams')
    teamtype = OpenTeam.portal_type
    allowed_types = tmtool.getAllowedTeamTypes()
    if teamtype not in allowed_types:
        print >> out, 'Adding %s to allowed team types' % teamtype
        allowed_types += (teamtype,)
        tmtool.setAllowedTeamTypes(allowed_types)

    mshiptype = OpenMembership.portal_type
    allowed_mships = tmtool.getAllowedMembershipTypes()
    if mshiptype not in allowed_mships:
        print >> out, 'Adding %s to allowed team membership types' % mshiptype
        allowed_mships += (mshiptype,)
        tmtool.setAllowedMembershipTypes(allowed_mships)
    if tmtool.getDefaultMembershipType() != mshiptype:
        print >> out, 'Setting %s to be default membership type' % mshiptype
        tmtool.setDefaultMembershipType(mshiptype)

@setuphandler
def addProjectsFolder(portal, out):
    if not 'projects' in portal.objectIds():
        print >> out, 'Creating projects folder'
        ttool = getToolByName(portal, 'portal_types')
        ttool.constructContent('Large Plone Folder', portal,
                               'projects', title='Projects')
        pfolder = portal._getOb('projects')
        wftool = getToolByName(portal, 'portal_workflow')

    pfolder = portal._getOb('projects')
    alsoProvides(pfolder, IAddProject)

    # Add type restrictions
    print >> out, 'Restricting addable types in Projects Folder'
    pfolder.setConstrainTypesMode(1)
    pfolder.setLocallyAllowedTypes(['OpenProject'])
    pfolder.setImmediatelyAddableTypes(['OpenProject'])

    # Install default policy

    pwf_tool = getToolByName(pfolder, 'portal_placeful_workflow')
    wf_config = pwf_tool.getWorkflowPolicyConfig(pfolder)
    if wf_config is None:
        print >> out, 'Setting default project security policy to Open'
        pfolder.manage_addProduct['CMFPlacefulWorkflow'].manage_addWorkflowPolicyConfig()
        wf_config = pwf_tool.getWorkflowPolicyConfig(pfolder)
        wf_config.setPolicyBelow(policy='open_policy')
        wf_tool = getToolByName(pfolder, 'portal_workflow')

@setuphandler
def setProjectFolderPermissions(portal, out):
    print >> out, 'Setting extra permissions in projects folder'
    pfolder = portal._getOb('projects')
    setPermissions(pfolder, DEFAULT_PFOLDER_PERMISSIONS_DATA, out)

@setuphandler
def setupProjectLayout(portal, out):
    print >> out, 'Setting projects folder view'
    pfolder = portal._getOb('projects')
    pfolder.setLayout('@@view')

@setuphandler
def setupHomeLayout(portal, out):
    print >> out, 'Setting home view'
    portal.setLayout('@@view')

@setuphandler
def setupPeopleFolder(portal, out):
    """
    set up the 'people' folder
    """
    oldname = 'Members'
    newname = 'people'
    newtitle = 'People'
    print >> out, 'Setting up "%s" folder' % newname
    obj_ids = portal.objectIds()
    if oldname in obj_ids:
        print >> out, '-> Renaming "%s" -> "%s"' % (oldname, newname)
        folder = portal._getOb(oldname)
        fti = folder.getTypeInfo()
        changeback = False
        if not fti.global_allow:
            oldvalue = fti.global_allow
            changeback = True
            fti.global_allow = True
        portal.manage_renameObject(oldname, newname)
        folder.setTitle(newtitle)
        if changeback:
            fti.global_allow = oldvalue
    elif not newname in obj_ids:
        print >> out, '-> Creating "%s" folder' % newname
        ttool = getToolByName(portal, 'portal_types')
        ttool.constructContent('Large Plone Folder', portal,
                               newname, title=newtitle)

    print >> out, '-> Setting "%s" as member area folder' % newname
    mtool = getToolByName(portal, 'portal_membership')
    mtool.setMembersFolderById(id=newname)
    if not mtool.getMemberareaCreationFlag():
        print >> out, '-> Setting member area creation flag'
        mtool.setMemberareaCreationFlag()

    # mark the people folder with an interface
    pf = getattr(portal, 'people')
    if not IAmAPeopleFolder.providedBy(pf):
        alsoProvides(pf, IAmAPeopleFolder)

    # set the default layout
    has_index = pf._getOb('index_html', None)
    if has_index:
        pf.manage_delObjects(['index_html'])
    pf.setDefaultPage(None)
    pf.setLayout('@@view')
    
@setuphandler
def migrateATDocToOpenPage(portal, out):
    print >> out, 'Migrating ATDocument type to OpenPage'
    if not 'migrate_atdoc_openpage' in portal.objectIds():
        portal.manage_addProduct['ExternalMethod'].manage_addExternalMethod(
            'migrate_atdoc_openpage', '', 'OpenPlans.migrate_atdoc_openpage',
            'migrate_atdoc_openpage')

    import transaction as txn
    txn.commit(1)
    print >> out, portal.migrate_atdoc_openpage(portal)
    portal.manage_delObjects(ids=['migrate_atdoc_openpage'])

@setuphandler
def setSiteIndexPage(portal, out):
    index_id = 'site-home'
    index_title = 'OpenPlans Home'
    if index_id not in portal.objectIds():
        print >> out, '-> creating site index page'
        portal.invokeFactory('Document', index_id, title=index_title)
        page = portal._getOb(index_id)
        page_file = pkg_resources.resource_stream(OPENCORE, 'copy/%s' %'site_index.html')
        page.setText(page_file.read())
        portal.setDefaultPage(index_id)

@setuphandler
def setCookieDomain(portal, out):
    app = portal.getPhysicalRoot()
    bid_mgr = app._getOb('browser_id_manager', None)
    if bid_mgr is not None:
        bid_mgr.setCookieDomain(config.COOKIE_DOMAIN)
        print >> out, "Set cookie domain to %s" % config.COOKIE_DOMAIN

@setuphandler
def setupTeamTool(portal, out):
    tmtool = getToolByName(portal, 'portal_teams')
    tmtool.setDefaultAllowedRoles(config.DEFAULT_ROLES)
    tmtool.setDefaultRoles(config.DEFAULT_ROLES[:1])
    tmtool.setDefaultActiveStates(config.DEFAULT_ACTIVE_MSHIP_STATES)

@setuphandler
def installCookieAuth(portal, out):
    
    uf = portal.acl_users

    print >> out, "signed cookie plugin setup"

    login_path = 'require_login'
    logout_path = 'logged_out'
    cookie_name = '__ac'

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
    print >> out, "Added Extended Cookie Auth Helper."
    from Products.PlonePAS.Extensions.Install import activatePluginInterfaces
    activatePluginInterfaces(portal, 'credentials_signed_cookie_auth', out)

    signed_cookie_auth = uf._getOb('credentials_signed_cookie_auth')
    if 'login_form' in signed_cookie_auth.objectIds():
        signed_cookie_auth.manage_delObjects(ids=['login_form'])
        print >> out, "Removed default login_form from signed cookie auth."
    signed_cookie_auth.cookie_name = cookie_name
    signed_cookie_auth.login_path = login_path

    old_cookie_auth = uf._getOb('credentials_cookie_auth', None)
    if old_cookie_auth is not None:
        old_cookie_auth.manage_activateInterfaces([])
        print >> out, "Deactivated unsigned cookie auth plugin"

    plugins = uf._getOb('plugins', None)
    if plugins is not None:
        plugins.movePluginsUp(IChallengePlugin,
                              ['credentials_signed_cookie_auth'],)
        print >> out, ("Move signed cookie auth to be top priority challenge "
                       "plugin")

@setuphandler
def installNewsFolder(portal, out):
    print >> out, ("Creating '%s' content" % 'news')
    existing_item = getattr(portal.aq_base, 'news', None)
    if existing_item is not None and existing_item.Type() != 'Folder':
        portal.manage_delObjects([existing_item.getId()])
        
    if getattr(portal.aq_base, 'news', None) is None:
        portal.invokeFactory('Folder', 'news', title='OpenPlans News')

    # mark the news folder with an interface
    pf = getattr(portal, 'news')
    if not IAmANewsFolder.providedBy(pf):
        alsoProvides(pf, IAmANewsFolder)

    # set the default view on the news folder
    pf.setLayout('@@view')

@setuphandler
def createValidationMember(portal, out):
    mdtool = getToolByName(portal, 'portal_memberdata')
    mem = OpenMember('validation_member')
    mdtool._validation_member = mem

def install_local_utility(iface, klass, name):
    def do_install(portal, out):
        setSite(portal) # specify the portal as the local utility context
        if queryUtility(iface) is not None:
            return
        sm = portal.getSiteManager()
        try:
            sm.registerUtility(iface, klass())
            print >> out, ('%s utility installed' %iface.__name__)
        except ValueError:
            old_utility = getattr(portal.utilities, iface.__name__)
            sm.registerUtility(iface, old_utility)
            print >> out, ('%s utility interface updated' %iface.__name__)
    do_install.__name__=name
    return setuphandler(do_install)

install_email_invites_utility = install_local_utility(IEmailInvites, EmailInvites, 'install_email_invites_utility')

@setuphandler
def addCatalogQueue(portal, out):
    q_id = 'portal_catalog_queue'
    if q_id not in portal.objectIds():
        print >> out, ('Adding portal_catalog_queue')
        f_disp = portal.manage_addProduct['QueueCatalog']
        f_disp.manage_addQueueCatalog(q_id)
        queue = portal._getOb(q_id)
        queue.setLocation('portal_catalog')

@setuphandler
def install_remote_auth_plugin(portal, out):
    plugin_id = 'opencore_remote_auth'
    uf = portal.acl_users
    if plugin_id in uf.objectIds():
        # plugin is already there, do nothing
        return
    print >> out, "Adding OpenCore remote auth plugin"
    openplans = uf.manage_addProduct['OpenPlans']
    openplans.manage_addOpenCoreRemoteAuth(plugin_id)
    activatePluginInterfaces(portal, plugin_id, out)

@setuphandler
def local_fqdn_return_address(portal, out):
    """
    If the boilerplate return address is there, we do a best-guess for
    a valid email_from_address hostname by using the local FQDN.
    """
    default = 'greetings@localhost.localdomain'
    if portal.getProperty('email_from_address') == default:
        addy = 'greetings@%s' % socket.getfqdn()
        portal.manage_changeProperties(email_from_address=addy)

@setuphandler
def setupKupu(portal, out):
    # this should really read from a config file
    # but for now, will do
    # this code taken from kupu source(plone config example)
    
    mt = getToolByName(portal, 'portal_membership')
    people = 'portal/%s/absolute_url' %mt.getMembersFolder().getId()

    people = dict(src='string:${%s}/kupucollection.xml' %people,
                  uri='string:${%s}' %people)
    [kl.update(people) for kl in kupu_libraries \
     if kl['id'] == 'people']

    typetool = getToolByName(portal, 'portal_types')
    def typefilter(types):
        all_meta_types = dict([ (t.id, 1) for t in typetool.listTypeInfo()])
        return [ t for t in types if t in all_meta_types ]
        
    kupu = getToolByName(portal, 'kupu_library_tool')
    libs = kupu.zmi_get_libraries()
    kupu.deleteLibraries(range(len(libs)))

    types = kupu.zmi_get_type_mapping()
    kupu.deleteResourceTypes([ t for (t,p) in types])

    for k,v in kupu_resource_map.items():
        kupu.addResourceType(k, typefilter(v))

    for lib in kupu_libraries:
        kupu.addLibrary(**lib)
        
    kupu.zmi_set_default_library('myitems')
    
    if out:
        print >> out, "Kupu setup completed"
