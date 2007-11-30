"""
for setup widgets for those annoying little tasks that
only need to happen occasionally
"""
from logging import getLogger

from Products.CMFCore import permissions as CMFCorePermissions
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import MigrationTool
from Products.CMFPlone.setup.SetupBase import SetupWidget
from Products.OpenPlans.workflows import PLACEFUL_POLICIES
from cStringIO import StringIO
from logging import getLogger
from migrate_membership_roles import migrate_membership_roles
from migrate_teams_to_projects import migrate_teams_to_projects
from opencore.interfaces.workflow import IReadWorkflowPolicySupport
from opencore.interfaces.workflow import IWriteWorkflowPolicySupport
from utils import setupKupu, reinstallSubskins
from zLOG import INFO, ERROR
from opencore.configuration.setuphandlers import \
     installWorkflowPolicies, securityTweaks, \
     migrateATDocToOpenPage, \
     setupProjectLayout, setCookieDomain, installCookieAuth, \
     setupPeopleFolder, setupProjectLayout, setupHomeLayout, \
     installNewsFolder, setProjectFolderPermissions

out = StringIO()
def convertFunc(func):
    """
    Turns one of our setuphandler functions into a portal_migrations
    setup widget.  The setuphandler functions have an 'orig' attribute
    containing an inner function; if we find one of these, that's what
    we really want to call.
    """
    realfn = getattr(func, 'orig', func)
    def new_func(portal):
        out=StringIO()
        realfn(portal, out)
        return out.getvalue()
    return new_func

def reinstallWorkflowPolicies(portal):
    pwftool = getToolByName(portal, 'portal_placeful_workflow')
    policies = set(pwftool.objectIds())
    deletes = policies.intersection(set(PLACEFUL_POLICIES.keys()))
    pwftool.manage_delObjects(ids=list(deletes))
    # have to unwrap it from the setuphandler decorator
    convertFunc(installWorkflowPolicies)(portal)

def migrate_listen_member_lookup(portal):
    from Products.listen.interfaces import IMemberLookup
    from zope.component import getUtility
    from opencore.listen.utility_overrides import OpencoreMemberLookup
    portal.utilities.manage_delObjects(['IMemberLookup'])
    opencore_memberlookup = OpencoreMemberLookup(portal)
    sm = portal.getSiteManager()
    sm.registerUtility(IMemberLookup, opencore_memberlookup)

def setup_nui(portal):
    """ this will call all the  nui setup functions """
    from opencore.nui.setup import nui_functions
    for fn in nui_functions.values():
        fn(portal)

def migrate_redirection(portal):
    from opencore.redirect import migrate_redirected_objects
    from opencore.interfaces import IProject
    from opencore.interfaces.member import IMemberFolder
    
    migrate_redirected_objects(portal.projects, IProject)
    migrate_redirected_objects(portal.people, IMemberFolder)
    
def fixProjectWFStates(portal):
    """
    make sure the projects are in the WF state that matches the
    chosen security policy
    """
    logger = getLogger('OpenPlans')
    cat = getToolByName(portal, 'portal_catalog')
    brains = cat(portal_type='OpenProject')
    for brain in brains:
        project = brain.getObject()
        policy_writer = IWriteWorkflowPolicySupport(project)
        policy_id = policy_writer.getCurrentPolicyId()
        # setting the policy to what it already is should now sync up the
        # project w/f state correctly
        policy_writer.setPolicy(policy_id)
        logger.log(INFO, 'set policy for %s project' % project.getId())

def initializeTeamWorkflow(portal):
    """
    initialize the teams with the new team workflow
    """
    cat = getToolByName(portal, 'portal_catalog')
    wftool = getToolByName(portal, 'portal_workflow')
    brains = cat(portal_type='OpenTeam')

    wfs = {}
    for wf_id in wftool.listWorkflows():
                wf = wftool.getWorkflowById(wf_id)
                wfs[wf_id] = wf

    for brain in brains:
        tm = brain.getObject()
        proj = tm.getProject()
        policy_reader = IReadWorkflowPolicySupport(proj)
        policy_id = policy_reader.getCurrentPolicyId()
        review_state = policy_id.split('_')[0]
        status = wftool.getStatusOf('openplans_team_workflow', tm).copy()
        if status.get('review_state') != review_state:
            status.update({'review_state': review_state, 'time': DateTime(),
                           'actor': 'admin',
                           'comments': 'Team permissions fixup'})
            wftool.setStatusOf('openplans_team_workflow', tm, status)

            # XXX: Bad Touching to avoid waking up the entire portal
            wftool._recursiveUpdateRoleMappings(tm, wfs)

def fixMembershipOwnership(portal):
    cat = getToolByName(portal, 'portal_catalog')
    uf = getToolByName(portal, 'acl_users')
    brains = cat(portal_type="OpenMembership")
    for brain in brains:
        mship = brain.getObject()
        owners = mship.users_with_local_role('Owner')
        if brain.getId not in mship.users_with_local_role('Owner'):
            mship.manage_delLocalRoles(owners)
            user = uf.getUserById(brain.getId)
            if user is not None:
                mship.changeOwnership(user)
                mship.manage_setLocalRoles(brain.getId, ('Owner',))


topp_functions = dict(
    setupKupu = convertFunc(setupKupu),
    setProjectListingLayout = convertFunc(setupProjectLayout),
    reinstallWorkflowPolicies = reinstallWorkflowPolicies,
    securityTweaks = convertFunc(securityTweaks),
    setProjectFolderPermissions = convertFunc(setProjectFolderPermissions),
    migrateATDocToOpenPage = convertFunc(migrateATDocToOpenPage),
    setCookieDomain = convertFunc(setCookieDomain),
    installCookieAuth=convertFunc(installCookieAuth),
    migrate_listen_member_lookup=migrate_listen_member_lookup,
    setupPeopleFolder=convertFunc(setupPeopleFolder),
    migrate_teams_to_projects=migrate_teams_to_projects,
    migrate_membership_roles=migrate_membership_roles,
    fixProjectWFStates=fixProjectWFStates,
    initializeTeamWorkflow=initializeTeamWorkflow,
    migrate_redirection=migrate_redirection,
    )

topp_functions["NUI Setup"]=setup_nui
topp_functions["Fix membership object ownership"] = fixMembershipOwnership

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
            out.append((self.functions[fn](self.portal),INFO))
            out.append(('Function %s has been applied' % fn, INFO))
        return out

    def installed(self):
        return []

    def available(self):
        """ Go get the functions """
        return self.functions.keys()


class NuiSetup(TOPPSetup):
    """ OpenPlans NUI Setup Bucket Brigade  """

    from opencore.nui.setup import nui_functions as functions
    type = 'NUI Setup'
    description = ' utillity methods for NUI site setup '
    #functions = nui_functions

    
MigrationTool.registerSetupWidget(TOPPSetup)
MigrationTool.registerSetupWidget(NuiSetup)
