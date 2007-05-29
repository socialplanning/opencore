"""
for setup widgets for those annoying little tasks that
only need to happen occasionally
"""
from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.setup.SetupBase import SetupWidget
from Products.CMFPlone import MigrationTool
from Products.Archetypes.public import listTypes
from Products.Archetypes.Extensions.utils import installTypes
from Products.Archetypes.Extensions.utils import install_subskin
from Products.OpenPlans import config
from Products.OpenPlans.workflows import PLACEFUL_POLICIES
from zLOG import INFO, ERROR

from utils import setupKupu

from Install import installColumns, fixUpEditTab, hideActions, \
     installWorkflows, setupPortalActions, addFormControllerOverrides, \
     installWorkflowPolicies, hideActionTabs, securityTweaks, uiTweaks, \
     migrateATDocToOpenPage, createIndexes, installZ3Types, registerJS, \
     setupProjectLayout, createMemIndexes, setCookieDomain, installCookieAuth, \
     setupPeopleFolder, setupProjectLayout, setupHomeLayout, \
     install_confirmation_workflow, installNewsFolder
from migrate_teams_to_projects import migrate_teams_to_projects
from migrate_membership_roles import migrate_membership_roles

from cStringIO import StringIO

try:
    set = set
except NameError:
    from sets import Set as set

from Products.OpenPlans.config import PROJECTNAME

out = StringIO()
def convertFunc(func):
    """
    turns a standard install function into a
    setup widget function
    """
    def new_func(self, portal):
        func(portal, out)
    #blank out
    out=StringIO()
    return new_func

def reinstallWorkflows(self, portal):
    wftool = getToolByName(portal, 'portal_workflow')
    qi = getToolByName(portal, 'portal_quickinstaller')
    product = getattr(qi, PROJECTNAME)
    wfs = product.getWorkflows()
    wftool.manage_delObjects(ids=wfs)
    out = StringIO()
    installWorkflows(portal, out)

def reinstallWorkflowPolicies(self, portal):
    pwftool = getToolByName(portal, 'portal_placeful_workflow')
    policies = set(pwftool.objectIds())
    deletes = policies.intersection(set(PLACEFUL_POLICIES.keys()))
    pwftool.manage_delObjects(ids=list(deletes))
    out = StringIO()
    installWorkflowPolicies(portal, out)

def reinstallTypes(self, portal):
    out = StringIO()
    installTypes(portal, out, listTypes(config.PROJECTNAME),
                 config.PROJECTNAME)
    hideActionTabs(portal, out)

def reinstallSubskins(self, portal):
    out = StringIO()
    install_subskin(portal, out, config.GLOBALS)

def migrate_listen_member_lookup(self, portal):
    from Products.listen.interfaces import IMemberLookup
    from zope.component import getUtility
    from opencore.listen.utility_overrides import OpencoreMemberLookup
    portal.utilities.manage_delObjects(['IMemberLookup'])
    opencore_memberlookup = OpencoreMemberLookup(portal)
    sm = portal.getSiteManager()
    sm.registerUtility(IMemberLookup, opencore_memberlookup)

def save_all_projects(portal, out):
    catalog = getToolByName(portal, 'portal_catalog')
    brains = catalog(portal_type='OpenProject')
    projects = (b.getObject() for b in brains)
    for project in projects:
        title = project.Title()
        values = dict(title=title)
        project.processForm(values=values)
        out.write('processed project: %s\n' % title)
    return out.getvalue()

def setup_nui(portal, out):
    """ this will call all the  nui setup functions """
    for fn in nui_functions.values():
        fn(portal, portal)

topp_functions = dict(
    setupKupu = convertFunc(setupKupu),
    fixUpEditTab = convertFunc(fixUpEditTab),
    installMetadataColumns = convertFunc(installColumns),
    setProjectListingLayout = convertFunc(setupProjectLayout),
    setupPortalActions = convertFunc(setupPortalActions),
    hideActions = convertFunc(hideActions),
    hideActionTabs = convertFunc(hideActionTabs),
    reinstallWorkflows = reinstallWorkflows,
    reinstallWorkflowPolicies = reinstallWorkflowPolicies,
    reinstallTypes = reinstallTypes,
    reinstallSubskins = reinstallSubskins,
    addFormControllerOverrides = convertFunc(addFormControllerOverrides),
    securityTweaks = convertFunc(securityTweaks),
    uiTweaks = convertFunc(uiTweaks),
    migrateATDocToOpenPage = convertFunc(migrateATDocToOpenPage),
    createIndexes = convertFunc(createIndexes),
    installZ3Types = convertFunc(installZ3Types),
    registerJS = convertFunc(registerJS),
    createMemIndexes = convertFunc(createMemIndexes),
    setCookieDomain = convertFunc(setCookieDomain),
    installCookieAuth=convertFunc(installCookieAuth),
    migrate_listen_member_lookup=migrate_listen_member_lookup,
    setupPeopleFolder=convertFunc(setupPeopleFolder),
    migrate_teams_to_projects=migrate_teams_to_projects,
    migrate_membership_roles=migrate_membership_roles,
    setup_nui=convertFunc(setup_nui)
    )

class TOPPSetup(SetupWidget):
    """ OpenPlans Setup Bucket Brigade  """

    type = 'TOPP Setup'
    functions = topp_functions
    description = ' utillity methods for TOPP site setup '

    def setup(self):
        pass

    def run(self, fn, **kwargs):
        out = []
        out.append((self.functions[fn](self, self.portal, **kwargs),INFO))
        out.append(('Function %s has been applied' % fn, INFO))
        return out

    def addItems(self, fns):
        out = []
        for fn in fns:
            out.append((self.functions[fn](self, self.portal),INFO))
            out.append(('Function %s has been applied' % fn, INFO))
        return out

    def installed(self):
        return []

    def available(self):
        """ Go get the functions """
        return self.functions.keys()

def reindex_membrane_tool(portal, out):
    # requires the types to be reinstalled first
    reinstallTypes(portal, portal)

    mbtool = getToolByName(portal, 'membrane_tool')
    mbtool.reindexIndex('getLocation', portal.REQUEST)

def move_interface_marking_on_projects_folder(portal, out):
    from zope.interface import directlyProvidedBy
    from zope.interface import directlyProvides
    from zope.interface import alsoProvides
    from opencore.interfaces import IAddProject
    import sys
    import opencore
    sys.modules['Products.OpenPlans.interfaces.adding'] = opencore.interfaces.adding
    pf = portal.projects
    directlyProvides(pf, directlyProvidedBy(pf) - IAddProject)
    alsoProvides(pf, IAddProject)


nui_functions = dict(install_confirmation_workflow=convertFunc(install_confirmation_workflow),
                     reindex_membrane_tool=convertFunc(reindex_membrane_tool),
                     move_interface_marking_on_projects_folder=convertFunc(move_interface_marking_on_projects_folder),
                     installNewsFolder=convertFunc(installNewsFolder),
                     setupPeopleFolder=convertFunc(setupPeopleFolder),
                     setupProjectLayout=convertFunc(setupProjectLayout),
                     setupHomeLayout=convertFunc(setupHomeLayout),
                     save_all_projects=convertFunc(save_all_projects),
                     )

class NuiSetup(TOPPSetup):
    """ OpenPlans NUI Setup Bucket Brigade  """

    type = 'NUI Setup'
    description = ' utillity methods for NUI site setup '
    functions = nui_functions
    
MigrationTool.registerSetupWidget(TOPPSetup)
MigrationTool.registerSetupWidget(NuiSetup)
