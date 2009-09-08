from Products.CMFCore.utils import getToolByName
from opencore.listen.interfaces import IListenContainer
from opencore.upgrades.utils import logger
from opencore.upgrades.utils import run_import_step

from zope.interface import alsoProvides

def mark_listen_folders(context):
    """
    Marks all 'lists' folders w/ the IListenContainer interface.
    """
    cat = getToolByName(context, 'portal_catalog')
    projs = cat.unrestrictedSearchResults(portal_type='OpenProject')
    for proj_brain in projs:
        proj = proj_brain.getObject()
        listfolder = proj._getOb('lists', None)
        if (listfolder is not None and
            not IListenContainer.providedBy(listfolder)):
            alsoProvides(listfolder, IListenContainer)
            logger.info('Marked folder with IListenContainer: %s'
                        % '/'.join(listfolder.getPhysicalPath()))


def bootstrap_member_deletion_queue(context):
    result = run_import_step(context, 'addMemberCleanupQueue')
    logger.info(result)
    

def add_sortable_title_membranetool_index(context):
    result = run_import_step(context, 'membranetool')
    logger.info('Reimported membrane tool from GS profile:\n%r' % result)
    
    getToolByName(context, 'membrane_tool').refreshCatalog()
    logger.info('Reindexed membrane_tool ZCatalog')
    
