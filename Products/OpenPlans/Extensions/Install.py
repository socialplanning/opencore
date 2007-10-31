import os
from StringIO import StringIO

from OFS.ObjectManager import BadRequestException

from zope.interface import alsoProvides
from zope.component import queryUtility
from zope.app.component.hooks import setSite

from Products.ZCatalog.ZCatalog import manage_addZCatalog
from Products.Five.site.localsite import enableLocalSiteHook
from Products.CMFCore import permissions
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.TypesTool import FactoryTypeInformation
from Products.CMFCore.Expression import Expression
from Products.Archetypes.Extensions.utils import install_subskin
from Products.Archetypes.public import listTypes
from Products.Archetypes.config import REFERENCE_CATALOG
from Products.Archetypes.Extensions.utils import installTypes#, install_subskin
from Products.membrane.config import TOOLNAME as MBTOOLNAME
from Products.remember.Extensions.workflow import addWorkflowScripts
from Products.remember.utils import getAdderUtility
from Products.CMFPlacefulWorkflow.PlacefulWorkflowTool import \
     WorkflowPolicyConfig_id
from Products.CMFEditions.Permissions import RevertToPreviousVersions
from Products.RichDocument.Extensions.utils import \
     registerAttachmentsFormControllerActions
from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin

from Products.OpenPlans import config
from Products.OpenPlans import content
from Products.OpenPlans.permissions import DEFAULT_PERMISSIONS_DATA
from Products.OpenPlans.permissions import DEFAULT_PFOLDER_PERMISSIONS_DATA
from Products.OpenPlans.permissions import PLACEFUL_PERMISSIONS_DATA
from Products.OpenPlans.content.team import OpenTeam
from Products.OpenPlans.utils import installDepends
from Products.OpenPlans.utils import add_form_controller_overrides
from Products.OpenPlans.utils import remove_form_controller_overrides
from Products.OpenPlans.workflows import default
from Products.OpenPlans.workflows import folder
from Products.OpenPlans.workflows import teamspace
from Products.OpenPlans.workflows import teammembership
from Products.OpenPlans.workflows import member
from Products.OpenPlans.workflows import team
from Products.OpenPlans.workflows import WORKFLOW_MAP
from Products.OpenPlans.workflows import PLACEFUL_POLICIES
from Products.OpenPlans.workflows import MEMBERSHIP_PLACEFUL_POLICIES
from Products.OpenPlans.Extensions.utils import setupKupu

from opencore.interfaces import IAddProject
from opencore.interfaces import IAmAPeopleFolder
from opencore.interfaces import IAmANewsFolder
from opencore.content.membership import OpenMembership
from opencore.content.member import OpenMember
from opencore.auth.SignedCookieAuthHelper import SignedCookieAuthHelper

from opencore.nui.member.interfaces import ITransientMessage
from opencore.nui.member.transient_messages import TransientMessage
from opencore.nui.project.interfaces import IEmailInvites
from opencore.nui.project.email_invites import EmailInvites


def installRoles(portal, out):
    """ Installs custom roles """
    vr = portal.validRoles()
    for role in config.DEFAULT_ROLES:
        if not role in vr:
            print >> out, "-> Adding '%s'" % role
            portal.manage_defined_roles(submit='Add Role',
                                        REQUEST={'role': role})
    tmtool = getToolByName(portal, 'portal_teams')
    tmtool.setDefaultAllowedRoles(config.DEFAULT_ROLES)
    tmtool.setDefaultRoles(config.DEFAULT_ROLES[:1])
    tmtool.setDefaultActiveStates(config.DEFAULT_ACTIVE_MSHIP_STATES)

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


def installZ3Types(portal, out):
    """ Installs types defined by z3 schemas """
    ttool = getToolByName(portal, 'portal_types')
    for f in content.z3ftis:
        if f['id'] not in ttool.objectIds():
            fti = FactoryTypeInformation(**f)
            ttool._setObject(f['id'], fti)
            print >> out, "Registered %s with the types tool" % f['id']

def install_workflow_map(portal, out, wfs=WORKFLOW_MAP):
    wf_tool = getToolByName(portal, 'portal_workflow')
    # First, change WF for MemberDataContainer to PortalWorkflow
    existing_wfs = wf_tool.objectIds()
    for wf in wfs.keys():
        if not wf in existing_wfs and wf != '(Default)':
            print >> out, '-> Adding %s' % wf
            wf_tool.manage_addWorkflow('%s (%s)' % (wf, wfs[wf][0]), wf)

            # XXX DCWorkflowDump doesn't yet support the 'manager_bypass'
            #     option.  when it does, the next 3 lines can be removed.
            if wf not in ('openplans_member_workflow',
                          'openplans_team_membership_workflow',
                          'closed_openplans_team_membership_workflow'):
                wfobj = wf_tool.getWorkflowById(wf)
                wfobj.manager_bypass = 1

        print >> out, '-> Assigning types to %s' % wf
        wf_tool.setChainForPortalTypes(wfs[wf][1], wf)
        if wf == 'openplans_member_workflow':
           addWorkflowScripts(wf_tool.getWorkflowById(wf))
    wf_tool.setDefaultChain('plone_openplans_workflow')

def installWorkflows(portal, out):
    """ Installs workflows """
    return install_workflow_map(portal, out)

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

def updateWorkflowRoleMappings(portal, out):
    wf_tool = getToolByName(portal, 'portal_workflow')
    wf_tool.updateRoleMappings()

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

def securityTweaks(portal, out):
    """ tweak site-wide security settings """
    print >> out, 'Modifying site security settings'
    for obj_path, obj_perms in PLACEFUL_PERMISSIONS_DATA.items():
        obj = portal.unrestrictedTraverse(obj_path)
        setPermissions(obj, obj_perms, out)

def setupSitePortlets(portal, out):
    print >> out, 'Portlet configuration:'

    print >> out, '-> Removing all site portlets'
    portal.manage_changeProperties(left_slots=tuple())
    portal.manage_changeProperties(right_slots=tuple())

    mdc = getToolByName(portal, 'portal_memberdata')
    print >> out, '-> Removing all portal_memberdata portlets'
    mdc.manage_changeProperties(left_slots=tuple())

def navTreeSetup(portal, out):
    nav_types = config.NAVTREE_TYPES
    portal.prefs_navigation_set(generated_tabs=False, portaltypes=nav_types)
    print >> out, '-> Navigation Tree types set'

def addprojectlistingview(portal, out):
    print >> out, 'Added project listing view'

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

def setMemberType(portal, out):
    mtype = 'OpenMember'
    print >> out, 'Specifying %s as default member type' % mtype
    adder = getAdderUtility(portal)
    adder.default_member_type = mtype

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

def setProjectFolderPermissions(portal, out):
    print >> out, 'Setting extra permissions in projects folder'
    pfolder = portal._getOb('projects')
    setPermissions(pfolder, DEFAULT_PFOLDER_PERMISSIONS_DATA, out)

def setupProjectLayout(portal, out):
    print >> out, 'Setting projects folder view'
    pfolder = portal._getOb('projects')
    pfolder.setLayout('@@view')

def setupHomeLayout(portal, out):
    print >> out, 'Setting home view'
    portal.setLayout('@@view')

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

def setSiteIndexPage(portal, out):
    index_id = 'site-home'
    index_title = 'OpenPlans Home'
    if index_id not in portal.objectIds():
        print >> out, '-> creating site index page'
        portal.invokeFactory('Document', index_id, title=index_title)
        page = portal._getOb(index_id)
        page_file = open(os.path.join(config.COPY_PATH,
                                      'site_index.html'), 'r')
        page.setText(page_file.read())
        portal.setDefaultPage(index_id)

def setCookieDomain(portal, out):
    app = portal.getPhysicalRoot()
    bid_mgr = app._getOb('browser_id_manager', None)
    if bid_mgr is not None:
        bid_mgr.setCookieDomain(config.COOKIE_DOMAIN)
        print >> out, "Set cookie domain to %s" % config.COOKIE_DOMAIN

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


def createValidationMember(portal, out):
    mdtool = getToolByName(portal, 'portal_memberdata')
    mem = OpenMember('validation_member')
    mdtool._validation_member = mem

def install_local_transient_message_utility(portal, out):
    setSite(portal) # specify the portal as the local utility context
    if queryUtility(ITransientMessage) is not None:
        return

    sm = portal.getSiteManager()
    sm.registerUtility(ITransientMessage, TransientMessage(portal))
    print >> out, ('Transient message utility installed')

def install_email_invites_utility(portal, out):
    setSite(portal) # specify the portal as the local utility context
    if queryUtility(IEmailInvites) is not None:
        return

    sm = portal.getSiteManager()
    sm.registerUtility(IEmailInvites, EmailInvites())
    print >> out, ('Email invites utility installed')

def addCatalogQueue(portal, out):
    q_id = 'portal_catalog_queue'
    if q_id not in portal.objectIds():
        print >> out, ('Adding portal_catalog_queue')
        f_disp = portal.manage_addProduct['QueueCatalog']
        f_disp.manage_addQueueCatalog(q_id)
        queue = portal._getOb(q_id)
        queue.setLocation('portal_catalog')

def install(self, migrate_atdoc_to_openpage=True):
    out = StringIO()
    portal = getToolByName(self, 'portal_url').getPortalObject()
    installDepends(self) # dependencies
    installWorkflowPolicies(portal, out) # placeful workflow stuff

    setCookieDomain(portal, out) # tweaks app root browser_id_manager
    installCookieAuth(portal, out) # adds auth plugin to PAS
    securityTweaks(portal, out) # placeful security changes (can go at root?)
    setMemberType(portal, out) # specifies default member type

    setTeamType(portal, out) # TeamSpace has no GS profile yet :-(
    addCatalogQueue(portal, out) # adds QueueCatalog instance to site root
    addProjectsFolder(portal, out) # adds 'projects' folder to site root
    setProjectFolderPermissions(portal, out) # more placeful security changes
    setupProjectLayout(portal, out) # sets layout setting on project folder
    setupPeopleFolder(portal, out) # various people folder tweaks
    setupKupu(portal, out) # various kupu tweaks
    if migrate_atdoc_to_openpage: # needed for unit test sanity
        migrateATDocToOpenPage(portal, out)

    setSiteIndexPage(portal, out) # creates site home and specifies as such
    setupVersioning(portal, out) # CMFEditions config
    installNewsFolder(portal, out) # adds / configures news folder
    createValidationMember(portal, out) # adds mem ob for use during validation
    install_local_transient_message_utility(portal, out) # adds local utility
    install_email_invites_utility(portal, out) # another local utility
    install_team_placeful_workflow_policies(portal, out) # placeful wf stuff
    print >> out, "Successfully installed %s." % config.PROJECTNAME
    return out.getvalue()
