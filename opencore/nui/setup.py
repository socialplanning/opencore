import os
from logging import getLogger, INFO
from pprint import pprint

from zope.component import getUtility

from topp.utils import config
from topp.featurelets.interfaces import IFeatureletSupporter, IFeatureletRegistry

from Products.CMFCore.utils import getToolByName

from Products.OpenPlans.Extensions.setup import convertFunc, reinstallTypes, \
     reinstallWorkflows
from Products.OpenPlans.Extensions.Install import install_workflow_map, \
     installNewsFolder, securityTweaks
from Products.OpenPlans.Extensions.Install import setupPeopleFolder, \
     setupProjectLayout, setupHomeLayout
from Products.OpenPlans.Extensions.Install import createMemIndexes, \
     installColumns, createValidationMember, \
     install_local_transient_message_utility, install_email_invites_utility
from Products.OpenPlans.Extensions.utils import reinstallSubskins
from Products.OpenPlans import config as op_config
from indexing import createIndexes
from DateTime import DateTime

logger = getLogger(op_config.PROJECTNAME)

HERE = os.path.dirname(__file__)
ALIASES = os.path.join(HERE, 'aliases.cfg')

def reindex_membrane_tool(portal):
    # requires the types to be reinstalled first
    reinstallTypes(portal)
    mbtool = getToolByName(portal, 'membrane_tool')
    mbtool.reindexIndex('getLocation', portal.REQUEST)
    logger.log(INFO, "getLocation reindexed")

def remove_roster_objects(portal):
    cat = getToolByName(portal, 'portal_catalog')
    roster_brains = cat(portal_type='OpenRoster')
    if not roster_brains:
        return
    flet_reg = getUtility(IFeatureletRegistry)
    flet = flet_reg.getFeaturelet('openroster')
    logger.log(INFO, 'Removing project rosters:')
    for brain in roster_brains:
        roster = brain.getObject()
        project = roster.aq_parent
        supporter = IFeatureletSupporter(project)
        supporter.removeFeaturelet(flet)
    logger.log(INFO, '%d rosters removed' % len(roster_brains))

def move_interface_marking_on_projects_folder(portal):
    #XX needed? test?
    from Products.Five.utilities.marker import erase
    from zope.interface import alsoProvides
    from opencore.interfaces import IAddProject
    import sys
    import opencore
    sys.modules['Products.OpenPlans.interfaces.adding'] = opencore.interfaces.adding
    pf = portal.projects
    erase(pf, IAddProject)
    alsoProvides(pf, IAddProject)
    logger.log(INFO, "Fixed up interfaces")

def migrate_wiki_attachments(portal):
    catalog = getToolByName(portal, 'portal_catalog')
    query = dict(portal_type='FileAttachment')
    brains = catalog(**query)
    objs = (b.getObject() for b in brains)
    logger.log(INFO, 'beginning attachment title migration')
    for attach in objs:
        if not attach.Title():
            attach_id = attach.getId()
            logger.log(INFO, 'Adding title to %s' % attach_id)
            attach.setTitle(attach_id)
    logger.log(INFO, 'attachment title migration complete')

def set_method_aliases(portal):
    pt = getToolByName(portal, 'portal_types')
    amap = config.ConfigMap.load(ALIASES)
    logger.log(INFO, 'Setting method aliases::')
    for type_name in amap:
        logger.log(INFO, '<< %s >>' %type_name)
        fti = getattr(pt, type_name)
        aliases = fti.getMethodAliases()
        new = amap[type_name]

        # compensate for cfgparser lowercasing
        if new.has_key('(default)'):
            new['(Default)']=new['(default)']
            del new['(default)']
            
        aliases.update(new)
        fti.setMethodAliases(aliases)
        logger.log(INFO, '%s' % str(aliases))

def migrate_portraits(portal):
    for member in portal.portal_memberdata.objectValues():
        if hasattr(member, 'portrait_thumb'):continue
        old_portrait = member.getPortrait()
        if old_portrait:
            member.setPortrait(old_portrait)

def migrate_mship_workflow_states(portal):
    catalog = getToolByName(portal, 'portal_catalog')
    mships = catalog(portal_type='OpenMembership', review_state='committed')
    wft = getToolByName(portal, 'portal_workflow')
    wfid = 'openplans_team_membership_workflow'
    mstool = getToolByName(portal, 'portal_membership')
    actor = mstool.getAuthenticatedMember().getId()
    timestamp = str(DateTime())
    for mship in mships:
        mship = mship.getObject()
        status = wft.getStatusOf(wfid, mship)
        status['review_state'] = 'public' # this is the important part
        status['actor'] = actor
        status['time'] = timestamp
        wft.setStatusOf(wfid, mship, status)
        mship.reindexObject(idxs=['review_state'])
    tmt = getToolByName(portal, 'portal_teams')
    tmt.setDefaultActiveStates(['public', 'private'])

def update_team_active_states(portal):
    logger.log(INFO, 'Updating team active states:')
    new_active_states = ('public', 'private')
    new_active_states_set = set(new_active_states)
    cat = getToolByName(portal, 'portal_catalog')
    brains = cat(portal_type='OpenTeam')
    for brain in brains:
        team = brain.getObject()
        if set(team.getActiveStates()) != new_active_states_set:
            logger.log(INFO, '--> updated active states for %s' % team.getId())
            team.setActiveStates(new_active_states)

nui_functions = dict(createMemIndexes=convertFunc(createMemIndexes),
                     installNewsFolder=convertFunc(installNewsFolder),
                     move_interface_marking_on_projects_folder=move_interface_marking_on_projects_folder,
                     reindex_membrane_tool=reindex_membrane_tool,
                     setupHomeLayout=convertFunc(setupHomeLayout),
                     setupPeopleFolder=convertFunc(setupPeopleFolder),
                     setupProjectLayout=convertFunc(setupProjectLayout),
                     securityTweaks=convertFunc(securityTweaks),
                     installMetadataColumns=convertFunc(installColumns),
                     reinstallSubskins=reinstallSubskins,
                     migrate_wiki_attachments=migrate_wiki_attachments,
                     createValidationMember=convertFunc(createValidationMember),
                     reinstallWorkflows=reinstallWorkflows,
                     setup_transient_message_utility=convertFunc(install_local_transient_message_utility),
                     install_email_invites_utility=convertFunc(install_email_invites_utility),
                     createIndexes=convertFunc(createIndexes),
                     )

nui_functions['Update Method Aliases'] = set_method_aliases
nui_functions['Migrate portraits (add new sizes)'] = migrate_portraits
nui_functions['Remove project roster objects'] = remove_roster_objects
nui_functions['Migrate memberships to new workflow'] = migrate_mship_workflow_states
nui_functions['Update team active states'] = update_team_active_states

def run_nui_setup(portal):
    pm = portal.portal_migration
    import transaction as txn
    pm.alterItems('TOPP Setup', items=['NUI_setup'])
    txn.commit()
    
