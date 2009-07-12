from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.OpenPlans import config
from Products.OpenPlans.content.team import OpenTeam
from Products.OpenPlans.permissions import DEFAULT_PFOLDER_PERMISSIONS_DATA
from Products.OpenPlans.permissions import PLACEFUL_PERMISSIONS_DATA
from Products.OpenPlans.workflows import MEMBERSHIP_PLACEFUL_POLICIES
from Products.OpenPlans.workflows import PLACEFUL_POLICIES
from Products.remember.utils import getAdderUtility
from StringIO import StringIO
from opencore.configuration import OC_REQ as OPENCORE
from opencore.content.member import OpenMember
from opencore.content.membership import OpenMembership
from opencore.interfaces import IAddProject
from opencore.interfaces import IAmANewsFolder
from opencore.interfaces import IAmAPeopleFolder
from opencore.interfaces.membership import IEmailInvites
from opencore.member.interfaces import REMOVAL_QUEUE_KEY
from opencore.project.browser.email_invites import EmailInvites
from opencore.utility.interfaces import IProvideSiteConfig
from plone.app.controlpanel.markup import IMarkupSchema
from zope.app.annotation import IAnnotations
from zope.app.component.hooks import setSite
from zope.component import queryUtility
from zope.interface import alsoProvides
import logging
import pkg_resources
import socket
import zc.queue


log = logging.getLogger('opencore.configuration.setuphandlers')

Z_DEPS = ('PlacelessTranslationService', 'Five', 'membrane', 'remember',
          'GenericSetup', 'CMFPlone', 'ManagableIndex', 'QueueCatalog',
          'SimpleAttachment', 'CacheSetup')

MEM_DEPS = ('membrane', 'remember')

DEPS = ('TeamSpace', 'CMFPlacefulWorkflow', 'RichDocument', 'listen',
        'CMFDiffTool', 'CMFEditions', 'PleiadesGeocoder'
       )

logger = None

def setuphandler(fn):
    """
    Decorator that turns QI functions into setuphandlers.
    """
    def execute_handler(context):
        stepname = fn.__name__
        handlers = context.readDataFile('opencore.txt')
        if handlers is None:
            return
        portal = context.getSite()
        out = StringIO()
        fn(portal, out)
        global logger
        logger = context.getLogger('opencore.configuration.setuphandlers')
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
    try:
        from opencore.feed.interfaces import ICanFeed
        if not ICanFeed.providedBy(pfolder):
            alsoProvides(pfolder, ICanFeed)
    except ImportError:
        pass

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

    setupProjectLayout(portal, out)
    setProjectFolderPermissions(portal, out)

def setProjectFolderPermissions(portal, out):
    print >> out, 'Setting extra permissions in projects folder'
    pfolder = portal._getOb('projects')
    setPermissions(pfolder, DEFAULT_PFOLDER_PERMISSIONS_DATA, out)

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
    try:
        from opencore.feed.interfaces import ICanFeed
        if not ICanFeed.providedBy(pf):
            alsoProvides(pf, ICanFeed)
    except ImportError:
        pass

    # set the default layout
    has_index = pf._getOb('index_html', None)
    if has_index:
        pf.manage_delObjects(['index_html'])
    pf.setDefaultPage(None)
    pf.setLayout('@@view')
    
@setuphandler
def migrateATDocToOpenPage(portal, out):
    print >> out, 'Migrating ATDocument type to OpenPage'
    from Products.OpenPlans.Extensions.migrate_atdoc_openpage import \
            migrate_atdoc_openpage
    print >> out, migrate_atdoc_openpage(portal)

@setuphandler
def setSiteIndexPage(portal, out):
    index_id = 'site-home'
    index_title = 'OpenPlans Home'
    if index_id not in portal.objectIds():
        print >> out, '-> creating site index page'
        portal.invokeFactory('Document', index_id, title=index_title)
        page = portal._getOb(index_id)
        page_file = pkg_resources.resource_stream(OPENCORE,
                                                  'copy/site_index.html')
        page.setText(page_file.read())
        portal.setDefaultPage(index_id)

@setuphandler
def setCookieDomain(portal, out):
    app = portal.getPhysicalRoot()
    bid_mgr = app._getOb('browser_id_manager', None)
    if bid_mgr is not None:
        setSite(portal)
        siteconfig = queryUtility(IProvideSiteConfig)
        # Hardcoded domain here is just a fallback.
        cookie_domain = siteconfig.get('cookie_domain', '.openplans.org')
        bid_mgr.setCookieDomain(cookie_domain)
        print >> out, "Set cookie domain to %s" % cookie_domain

@setuphandler
def setupTeamTool(portal, out):
    tmtool = getToolByName(portal, 'portal_teams')
    tmtool.setDefaultAllowedRoles(config.DEFAULT_ROLES)
    tmtool.setDefaultRoles(config.DEFAULT_ROLES[:1])
    tmtool.setDefaultActiveStates(config.DEFAULT_ACTIVE_MSHIP_STATES)

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
    if getattr(mdtool.aq_base, '_validation_member', None) is not None:
        # already exists
        return

    mem = OpenMember('validation_member')
    from Products.remember.permissions import EDIT_SECURITY_PERMISSION
    mem.getField('password').write_permission = EDIT_SECURITY_PERMISSION
    mdtool._validation_member = mem

def register_local_utility(portal, out, iface, klass, factory_fn=None,
                           replace=False):
    setSite(portal) # specify the portal as the local utility context
    sm = portal.getSiteManager()
    util = queryUtility(iface)
    if  util is not None:
        if not replace:
            return
        sm.unregisterUtility(component=util, provided=iface)
    try:
        if factory_fn is not None:
            obj = factory_fn()
        else:
            obj = klass()
        sm.registerUtility(obj, iface)
        print >> out, ('%s utility installed' %iface.__name__)
    except ValueError:
        # re-register object
        old_utility = aq_inner(getattr(portal.utilities, iface.__name__))
        portal.utilities._delObject(iface.__name__, suppress_events=True)
        alsoProvides(old_utility, iface)
        sm.registerUtility(iface, old_utility)
        print >> out, ('%s utility interface updated' %iface.__name__)

def migrate_local_utility_iface(portal, out, iface, old_iface=None, klass=None):
    """re-register object w/ an iface of same name"""
    setSite(portal) # specify the portal as the local utility context
    sm = portal.getSiteManager()

    if old_iface is None:
        # sometimes you just moved the interface but they are
        # equivalent. This finds the first iface of the same name
        old_iface = retrieve_orphaned_iface(iface, sm.utilities)

    old_utility = sm.queryUtility(old_iface)
    if klass is not None:
        # optional assertion 
        # if this misses we might have a big problem
        assert isinstance(old_utility, klass), "Classes do not match"

    alsoProvides(old_utility, iface) # necessary?
    sm.unregisterUtility(old_utility, old_iface)
    sm.registerUtility(old_utility, iface)
    print >> out, ('%s utility interface updated' %iface.__name__)

def retrieve_orphaned_iface(new_iface, reg):
    # bad touch
    for iface in reg._adapters[0].keys():
        if iface.__name__ == new_iface.__name__:
            return iface

@setuphandler
def install_email_invites_utility(portal, out):
    register_local_utility(portal, out, IEmailInvites, EmailInvites)

@setuphandler
def migrate_listen_member_lookup(portal, out):
    from Products.listen.interfaces import IMemberLookup
    from opencore.listen.utility_overrides import OpencoreMemberLookup
    def LookupFactory():
        return OpencoreMemberLookup(portal)
    register_local_utility(portal, out, IMemberLookup, OpencoreMemberLookup,
                           factory_fn=LookupFactory, replace=True)

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
def activate_wicked(portal, out):
    """
    Turn on wicked's wiki linking.
    """
    # we don't use Plone's allowable types infrastructure, so we
    # just set any type to turn on the wiki linking
    markup_ctrl = IMarkupSchema(portal, None)
    if markup_ctrl is None:
        setSite(portal) # <-- req'd when called via 'zopectl run'
        markup_ctrl = IMarkupSchema(portal)
    if not markup_ctrl.wiki_enabled_types:
        print >> out, "Activating wicked linking"
        markup_ctrl.wiki_enabled_types = ['Page']

@setuphandler
def bootstrap_member_deletion_queue(portal, out):
    annot = IAnnotations(portal)
    if annot.has_key(REMOVAL_QUEUE_KEY):
        print >> out, 'Already have member deletion queue, skipping'
        return
    annot[REMOVAL_QUEUE_KEY] = zc.queue.Queue()
    print >> out, "Added member deletion queue"
    return
