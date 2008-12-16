"""
This should be run after upgrading from opencore 0.14.X
to opencore >= 0.15.0.
"""

from Products.CMFCore.utils import getToolByName
from opencore.upgrades.utils import logger
from opencore.upgrades.utils import run_import_step

def reapply_type_information(context):
    result = run_import_step(context, 'typeinfo')
    logger.info(result)

def reapply_workflow_profile(context):
    result = run_import_step(context, 'workflow')
    logger.info(result)

def update_workflow_permissions(context):
    wftool = getToolByName(context, 'portal_workflow')
    wftool.updateRoleMappings()

def update_rolemap(context):
    result = run_import_step(context, 'rolemap')
    logger.info(result)

def retitle_member_areas(context):
    """change the title of the member areas on the site to use
    member title instead of member id"""
    # forward-ported from the people-cloud branch.
    portal = getToolByName(context, 'portal_url').getPortalObject()
    mdtool = getToolByName(portal, 'portal_memberdata')
    mem_ids = dict.fromkeys(mdtool.objectIds(spec='OpenMember'))
    pfolder = portal.people
    for mem_id, home in pfolder.objectItems():
        if mem_id in mem_ids:
            member = mdtool._getOb(mem_id)
            mem_title = member.Title() or mem_id
            if mem_title != mem_id:
                home.setTitle(mem_title)
                home.reindexObject(idxs=['Title'])
                logger.info('retitled folder for %s' % mem_id)
            page = home._getOb('%s-home' % mem_id, None)
            if page is not None and page.Title() == '%s Home' % mem_id:
                page.setTitle('%s Home' % mem_title)
                page.reindexObject(idxs=['Title'])
                logger.info('retitled home page for %s' % mem_id)
