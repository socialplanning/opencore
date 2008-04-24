from opencore.browser.naming import get_view_names
import logging

logger = logging.getLogger("opencore.upgrades")

profile_id = 'opencore.configuration:default'

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

def run_import_step(setup_tool, step_id, profile_id=profile_id,
                    run_deps=False, purge_old=None):
    """ run an import step via the setup tool """
    result = setup_tool.runImportStepFromProfile('profile-%s' % profile_id,
                                                 step_id,
                                                 run_dependencies=run_deps,
                                                 purge_old=purge_old,
                                                 )
    return result
