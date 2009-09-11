from Acquisition import aq_base
from opencore.browser.naming import get_view_names
import logging
import transaction

logger = logging.getLogger("opencore.upgrades")

def default_profile_id():
    from opencore.utility.interfaces import IProvideSiteConfig
    from zope.component import getUtility

    configparser = getUtility(IProvideSiteConfig)
    etc_svn_subdir = configparser.get('etc_svn_subdir')
    return 'opencore.configuration:%s' % etc_svn_subdir

def move_blocking_content(portal):
    """
    Renames all portal content that is masking a view defined on
    project objects due to namespace collisions.
    """
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

def rerun_import_steps(context, steps):
    """
    Reimport any import steps that need to be reapplied to the site.

    Ideally, GenericSetup would provide a ZCML tag for this, but it's
    not there yet.

    'steps' is a dictionary of the import steps to be run.  Keys
    should be the import step id.  The value for each key should be a
    dictionary that may contain other parameters to be passed in to
    the import step ('purge_old' is the only one currently supported).
    An example dictionary might look like this:

    steps = {'activate_wicked': dict(),
             'typeinfo': dict(purge_old=True),
             'controlpanel': dict(),
             'languagetool': dict(),
             }
    """
    request = context.REQUEST
    profile_id = request.form.get('profile_id')
    if not profile_id:
        profile_id = default_profile_id()

    for step_id in steps:
        purge = steps.get(step_id).get('purge_old', None)
        result = run_import_step(context, step_id,
                                 profile_id=profile_id,
                                 purge_old=purge)
        logger.info(result)
    ran_steps = ', '.join(steps.keys())
    print 'done importing selected steps: %s' % ran_steps

def run_import_step(setup_tool, step_id, profile_id=None,
                    run_deps=False, purge_old=None):
    """ run an import step via the setup tool """
    
    if profile_id is None:
        profile_id = default_profile_id()

    result = setup_tool.runImportStepFromProfile('profile-%s' % profile_id,
                                                 step_id,
                                                 run_dependencies=run_deps,
                                                 purge_old=purge_old,
                                                 )
    return result


def updateRoleMappings(portal, commit_interval=10):
    """
    An alternate implementation of the workflow tool's updateRoleMappings
    behaviour that commits the transaction frequently to prevent
    inevitable conflict errors from such a long-running process.
    """
    wft = portal.portal_workflow
    wfs = {}
    for id in wft.objectIds():
        wf = wft.getWorkflowById(id)
        if hasattr(aq_base(wf), 'updateRoleMappingsFor'):
            wfs[id] = wf
    count = _recursiveUpdateRoleMappings(portal, wfs, wft,
                                         commit_interval=commit_interval)
    # One more commit to get any leftovers.
    transaction.get().note("Workflow Tool role mappings update COMPLETE: %s"
                           % count)
    transaction.commit()
    return count

def _recursiveUpdateRoleMappings(ob, wfs, wft, count=0, commit_interval=10):
    # wfs = workflows; wft = portal_workflow tool.
    wf_ids = wft.getChainFor(ob)
    if wf_ids:
        changed = 0
        for wf_id in wf_ids:
            wf = wfs.get(wf_id, None)
            if wf is not None:
                did = wf.updateRoleMappingsFor(ob)
                if did:
                    changed = 1
        if changed:
            count += 1
            if hasattr(aq_base(ob), 'reindexObject'):
                # Reindex security-related indexes
                try:
                    ob.reindexObject(idxs=['allowedRolesAndUsers'])
                except TypeError:
                    # Catch attempts to reindex portal_catalog.
                    pass
            if count % commit_interval == 0:
                msg = "Workflow Tool role mappings update: committed %d" % count
                transaction.get().note(msg)
                transaction.commit()
                logger.info('==== %s ====' % msg)

    if hasattr(aq_base(ob), 'objectItems'):
        obs = ob.objectItems()
        if obs:
            for k, v in obs:
                changed = getattr(v, '_p_changed', 0)
                count = _recursiveUpdateRoleMappings(v, wfs, wft, count,
                                                     commit_interval)
                if changed is None:
                    # Re-ghostify.
                    v._p_deactivate()
    return count
