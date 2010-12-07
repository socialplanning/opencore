from Products.CMFCore.utils import getToolByName
from opencore.listen.interfaces import IListenContainer
from opencore.upgrades.utils import logger
from opencore.upgrades.utils import run_import_step

from zope.interface import alsoProvides

def add_mailing_list_subscribers_index(setup_tool):
    profile_id = setup_tool.REQUEST.form.get('profile_id')
    result = run_import_step(setup_tool, 'catalog', profile_id=profile_id)
    logger.info('Reimported portal_catalog from GS profile:\n%r' % result)
    
    getToolByName(setup_tool, 'portal_catalog').refreshCatalog()
    logger.info('Reindexed portal_catalog ZCatalog')
