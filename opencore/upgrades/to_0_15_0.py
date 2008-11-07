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
