import os
from logging import getLogger, INFO
from pprint import pprint

from zope.component import getUtility
from zope.interface import alsoProvides

from borg.localrole.utils import setup_localrole_plugin

from topp.utils import config
from topp.featurelets.interfaces import IFeatureletSupporter, IFeatureletRegistry

from Products.CMFCore.utils import getToolByName
from Products.PortalTransforms.libtransforms.utils import MissingBinary
from Products.CMFEditions.interfaces.IArchivist import ArchivistRetrieveError

from Products.OpenPlans.Extensions.setup import convertFunc, reinstallTypes, \
     reinstallWorkflows, reinstallWorkflowPolicies
from Products.OpenPlans.Extensions.Install import install_workflow_map, \
     installNewsFolder, securityTweaks
from Products.OpenPlans.Extensions.Install import setupPeopleFolder, \
     setupProjectLayout, setupHomeLayout
from Products.OpenPlans.Extensions.Install import createMemIndexes, \
     installColumns, createValidationMember, \
     install_local_transient_message_utility, install_email_invites_utility
from Products.OpenPlans.Extensions.Install import setCaseInsensitiveLogins, \
     setSiteEmailAddresses, updateWorkflowRoleMappings
from Products.OpenPlans.Extensions.Install import install_remote_auth_plugin, \
     install_team_placeful_workflow_policies, addCatalogQueue
from Products.OpenPlans.Extensions.utils import reinstallSubskins
from Products.OpenPlans import config as op_config
from indexing import createIndexes
from DateTime import DateTime
from topp.featurelets.interfaces import IFeatureletSupporter
from opencore.interfaces import IOpenPage, INewsItem
from opencore.nui.project.metadata import _update_last_modified_author
from opencore.nui.wiki.add import get_view_names
from Products.OpenPlans.content.project import OpenProject
from persistent import mapping

logger = getLogger(op_config.PROJECTNAME)

HERE = os.path.dirname(__file__)
ALIASES = os.path.join(HERE, 'aliases.cfg')


def move_blocking_content(portal):
    try:
        proj = portal.projects[portal.projects.objectIds()[1]]
    except IndexError:
        return
    names = get_view_names(proj, ignore_dummy=True)
    projects_path = '/'.join(portal.projects.getPhysicalPath())
    blockers = portal.portal_catalog(getId=list(names), path=projects_path)
    for blocker in blockers:
        obj = blocker.getObject()
        parent = obj.aq_parent
        id_ = obj.getId()
        if parent != portal.projects:
            new_id = "%s-page" % id_
            parent.manage_renameObjects([obj.getId()], [new_id])


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
    logger.log(INFO, "Updating memberships' workflow states:")
    catalog = getToolByName(portal, 'portal_catalog')
    mships = catalog(portal_type='OpenMembership', review_state='committed')
    wft = getToolByName(portal, 'portal_workflow')
    pwft = getToolByName(portal, 'portal_placeful_workflow')
    mstool = getToolByName(portal, 'portal_membership')
    actor = mstool.getAuthenticatedMember().getId()
    timestamp = str(DateTime())
    for mship in mships:
        mship = mship.getObject()
        config = pwft.getWorkflowPolicyConfig(mship)
        wfids = config.getPlacefulChainFor('OpenMembership')
        wfid = wfids[0]
        status = wft.getStatusOf(wfid, mship)
        status['review_state'] = 'public' # this is the important part
        status['actor'] = actor
        status['time'] = timestamp
        wft.setStatusOf(wfid, mship, status)
        mship.reindexObject(idxs=['review_state'])
        logger.log(INFO, '--> updated workflow state for %s' % mship.getId())
    logger.log(INFO, "Done updating memberships' workflow states.")

def migrate_mships_made_active_date(portal):
    logger.log(INFO, "Updating memberships' made_active_date attribute:")
    catalog = getToolByName(portal, 'portal_catalog')
    mships = catalog(portal_type='OpenMembership')
    for mship in mships:
        mship = mship.getObject()
        if not hasattr(mship, 'made_active_date'):
            setattr(mship, 'made_active_date', mship.creation_date)
            logger.log(INFO, '--> updated made_active_date for %s' % mship.getId())
        mship.reindexObject(idxs=['made_active_date'])
    logger.log(INFO, "Done updating memberships' made_active_date attribute.")

def migrate_mission_statement(portal):
    catalog = getToolByName(portal, 'portal_catalog')
    proj_brains = catalog(portal_type='OpenProject')
    for proj in (b.getObject() for b in proj_brains):
        home_page = proj.getDefaultPage()
        page = proj.unrestrictedTraverse(home_page)
        description = page.Description()
        if description:
            proj.setDescription(description)

def migrate_page_descriptions(portal):
    catalog = getToolByName(portal, 'portal_catalog')
    page_brains = catalog(portal_type='Document')
    for brain in page_brains:
        description = brain.Description
        if not description: continue
        page = brain.getObject()
        textunit = page.getField('text').get(page, raw=True)
        if textunit.isBinary(): continue
        body = page.getRawText()
        new_body = '<p><b>%s</b></p>\n%s' % (description, body)
        page.setText(new_body)
        # override the description, so running this migration
        # multiple times is safe
        page.setDescription('')
        page.reindexObject(idxs=['Description', 'SearchableText'])

def update_team_active_states(portal):
    logger.log(INFO, 'Updating team active states:')
    new_active_states = ('public', 'private')
    new_active_states_set = set(new_active_states)

    tmt = getToolByName(portal, 'portal_teams')
    if set(tmt.getDefaultActiveStates()) != new_active_states_set:
        tmt.setDefaultActiveStates(new_active_states)

    cat = getToolByName(portal, 'portal_catalog')
    brains = cat(portal_type='OpenTeam')
    for brain in brains:
        team = brain.getObject()
        if set(team.getActiveStates()) != new_active_states_set:
            logger.log(INFO, '--> updated active states for %s' % team.getId())
            team.setActiveStates(new_active_states)

def fix_case_on_featurelets(portal):
    cat = getToolByName(portal, 'portal_catalog')
    brains = cat(portal_type='OpenProject')
    for brain in brains:
        project = brain.getObject()
        flet_supporter = IFeatureletSupporter(project)
        listen_storage = flet_supporter.storage.get('listen', None)
        if listen_storage:
            # we have to make a complete copy of the date structure
            listen_storage = dict(listen_storage)
            listen_storage['content'][0]['title'] = 'Mailing lists'
            listen_storage['menu_items'][0]['title'] = u'Mailing lists'
            listen_storage['menu_items'][0]['description'] = u'Mailing lists'

            # setting the new values triggers persistence
            flet_supporter.storage['listen']=listen_storage
        tt_storage = flet_supporter.storage.get('tasks', None)
        if tt_storage:
            tt_storage=dict(tt_storage)
            tt_storage['menu_items'][0]['title'] = u'Tasks'
            tt_storage['menu_items'][0]['description'] = u'Task tracker'
            flet_supporter.storage['tasks']=tt_storage

def annotate_last_modified_author(portal):
    from opencore.nui.project.metadata import ANNOT_KEY
    pr = getToolByName(portal, 'portal_repository')
    cat = getToolByName(portal, 'portal_catalog')

    # sort all pages in ascending order so project updates
    # will make sense
    all_documents = cat(portal_type='Document')
    all_documents = sorted(all_documents, key=lambda b:b.ModificationDate)

    for page in (b.getObject() for b in all_documents):

        if not IOpenPage.providedBy(page): continue

        try:
            histories = pr.getHistory(page, countPurged=False)
            last_history = histories[0]
            last_author = last_history.sys_metadata.get('principal', None)
            if last_author is None: continue

            _update_last_modified_author(page, user_id=last_author)

        except ArchivistRetrieveError:
            # we get an error if there is no history
            # (like for our test content)
            pass

def markNewsItems(portal):
    cat = getToolByName(portal, 'portal_catalog')
    path = '/'.join([portal.absolute_url_path(), 'news'])
    brains = cat(path=path, portal_type='Document')
    for brain in brains:
        ni = brain.getObject()
        if not INewsItem.providedBy(ni):
            alsoProvides(ni, INewsItem)

from Products.Archetypes.utils import OrderedDict

# make rest of names readable  (maybe use config system)
nui_functions = OrderedDict()
nui_functions['Install borg.localrole PAS plug-in'] = setup_localrole_plugin
nui_functions['Add Catalog Queue'] = convertFunc(addCatalogQueue)
nui_functions['Move Blocking Content'] = move_blocking_content
nui_functions['Create Member Indexes'] = convertFunc(createMemIndexes)
nui_functions['installNewsFolder'] = convertFunc(installNewsFolder)
nui_functions['move_interface_marking_on_projects_folder'] = move_interface_marking_on_projects_folder
nui_functions['setupHomeLayout'] = convertFunc(setupHomeLayout)
nui_functions['setupPeopleFolder'] = convertFunc(setupPeopleFolder)
nui_functions['setupProjectLayout'] = convertFunc(setupProjectLayout)
nui_functions['securityTweaks'] = convertFunc(securityTweaks)
nui_functions['installMetadataColumns'] = convertFunc(installColumns)
nui_functions['reinstallSubskins'] = reinstallSubskins
nui_functions['migrate_wiki_attachments'] = migrate_wiki_attachments
nui_functions['createValidationMember'] = convertFunc(createValidationMember)
nui_functions['reinstallWorkflows'] = reinstallWorkflows
nui_functions['reinstallWorkflowPolicies'] = reinstallWorkflowPolicies
nui_functions['setup_transient_message_utility'] = convertFunc(install_local_transient_message_utility)
nui_functions['install_email_invites_utility'] = convertFunc(install_email_invites_utility)
nui_functions['migrate_mission_statement'] = migrate_mission_statement
nui_functions['createIndexes'] = convertFunc(createIndexes)
nui_functions['migrate_page_descriptions'] = migrate_page_descriptions
nui_functions['fix_case_on_featurelets'] = fix_case_on_featurelets
nui_functions['reindex_membrane_tool'] = reindex_membrane_tool

nui_functions['Update Method Aliases'] = set_method_aliases
nui_functions['Migrate portraits (add new sizes)'] = migrate_portraits
nui_functions['Remove project roster objects'] = remove_roster_objects
nui_functions['Install default team workflow policy'] = convertFunc(install_team_placeful_workflow_policies)
nui_functions['Migrate memberships to new workflow'] = migrate_mship_workflow_states
nui_functions['Update team active states'] = update_team_active_states
nui_functions['Add made_active_date attribute to memberships'] = migrate_mships_made_active_date
nui_functions['Set case insensitive logins'] = convertFunc(setCaseInsensitiveLogins)
nui_functions['Set site email addresses'] = convertFunc(setSiteEmailAddresses)
nui_functions['annotate last modified author'] = annotate_last_modified_author
nui_functions["Propagate workflow security settings"] = \
                         convertFunc(updateWorkflowRoleMappings)
nui_functions['markNewsItems'] = markNewsItems
nui_functions['Install OpenCore Remote Auth Plugin'] = \
                       convertFunc(install_remote_auth_plugin)

def run_nui_setup(portal):
    pm = portal.portal_migration
    import transaction as txn
    pm.alterItems('TOPP Setup', items=['NUI_setup'])
    txn.commit()
    
