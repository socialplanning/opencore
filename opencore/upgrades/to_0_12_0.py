from Products.CMFCore.utils import getToolByName
from opencore.upgrades.utils import run_import_step
from opencore.upgrades.utils import logger
from opencore.upgrades.utils import default_profile_id

def import_opencore_profile(context):
    """
    Re-imports the entire opencore GenericSetup profile for this site.
    """
    setuptool = getToolByName(context, 'portal_setup')
    setuptool.runAllImportStepsFromProfile('profile-%s' % default_profile_id)

def fixup_list_lookup_utility(context):
    """
    Makes sure listen's IListLookup utility is installed at the portal
    level.
    """
    result = run_import_step(context, 'componentregistry',
                             profile_id='Products.listen:listen',
                             )
    logger.info(result)
