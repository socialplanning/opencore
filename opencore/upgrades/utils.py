from fassembler.configparser import configparser
from opencore.browser.naming import get_view_names
import logging

logger = logging.getLogger("opencore.upgrades")

etc_svn_subdir = configparser.get_config('etc_svn_subdir')
default_profile_id = 'opencore.configuration:%s' % etc_svn_subdir

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
        profile_id = default_profile_id
    for step_id in steps:
        purge = steps.get(step_id).get('purge_old', None)
        result = run_import_step(context, step_id,
                                 profile_id=profile_id,
                                 purge_old=purge)
        logger.info(result)
    ran_steps = ', '.join(steps.keys())
    print 'done importing selected steps: %s' % ran_steps

def run_import_step(setup_tool, step_id, profile_id=default_profile_id,
                    run_deps=False, purge_old=None):
    """ run an import step via the setup tool """
    result = setup_tool.runImportStepFromProfile('profile-%s' % profile_id,
                                                 step_id,
                                                 run_dependencies=run_deps,
                                                 purge_old=purge_old,
                                                 )
    return result
