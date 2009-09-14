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


def bootstrap_member_deletion_queue(setup_tool):
    profile_id = setup_tool.REQUEST.form.get('profile_id')
    result = run_import_step(setup_tool, 'addMemberCleanupQueue', profile_id=profile_id)
    logger.info(result)
    

def add_sortable_title_membranetool_index(setup_tool):
    profile_id = setup_tool.REQUEST.form.get('profile_id')
    result = run_import_step(setup_tool, 'membranetool', profile_id=profile_id)
    logger.info('Reimported membrane tool from GS profile:\n%r' % result)
    
    getToolByName(setup_tool, 'membrane_tool').refreshCatalog()
    logger.info('Reindexed membrane_tool ZCatalog')
    
def declare_supported_languages(setup_tool):
    profile_id = setup_tool.REQUEST.form.get('profile_id')
    result = run_import_step(setup_tool, 'languagetool', profile_id=profile_id)
    logger.info('Reimported portal_languages tool from GS profile:\n%s' % result)
