"""
This should be run after upgrading from opencore 0.14.X
to opencore >= 0.15.0.
"""

from Products.CMFCore.utils import getToolByName
from opencore.upgrades.utils import logger
from opencore.upgrades.utils import run_import_step
import transaction

def reapply_type_information(context):
    result = run_import_step(context, 'typeinfo')
    logger.info(result)

def reapply_workflow_profile(context):
    result = run_import_step(context, 'workflow')
    logger.info(result)

def update_workflow_permissions(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    from utils import updateRoleMappings
    updateRoleMappings(portal, commit_interval=50)

def update_rolemap(context):
    result = run_import_step(context, 'rolemap')
    logger.info(result)

def retitle_member_areas(context):
    """change the title of the member areas on the site to use
    member title instead of member id"""
    # forward-ported from the people-cloud branch.
    portal = getToolByName(context, 'portal_url').getPortalObject()
    mdtool = getToolByName(portal, 'portal_memberdata')
    mem_ids = dict.fromkeys(
        mdtool.objectIds(spec='OpenMember'))
    i = 0
    changed = False
    for mem_id, home in portal.people.objectItems():
        if mem_id not in mem_ids:
            continue
        i += 1
        member = mdtool._getOb(mem_id)
        mem_title = member.Title() or mem_id
        if home.Title() != mem_title:
            # This is used in top nav.
            # It's not directly user-controllable, so we always do the upgrade
            changed = True
            home.setTitle(mem_title)
            home.reindexObject(idxs=['Title'])
            logger.info('retitled folder for %s' % mem_id)
        page = home._getOb('%s-home' % mem_id, None)
        if page is not None and page.Title() == '%s Home' % mem_id and mem_id != mem_title:
            # Pages are user-renamable so we had to check for a nonstandard title
            changed = True
            page.setTitle('%s Home' % mem_title)
            page.reindexObject(idxs=['Title'])
            logger.info('retitled home page for %s' % mem_id)
        if changed and i % 400 == 0:
            transaction.commit()
            logger.info('===== COMMITTING (%d of %d) ====' %(i, len(mem_ids)))
            changed = False
    transaction.commit()
    logger.info('==== COMMITTING (%d of %d) ====' %(i, len(mem_ids)))
