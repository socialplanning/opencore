from opencore.upgrades.utils import run_import_step
from opencore.upgrades.utils import profile_id as default_profile_id
from opencore.upgrades.utils import logger
from zope.app.component.hooks import setSite
from Products.CMFCore.utils import getToolByName
from Products.Five.site.localsite import disableLocalSiteHook

#####
# 'steps' is a dictionary of import steps that need to be re-run in this
# migration.  keys are the import step id, value is a dictionary that may
# contain other parameters to be passed in to the import step (purge_old
# is the only one currently supported).
#####
steps = {'activate_wicked': dict(),
         'typeinfo': dict(purge_old=True),
         'controlpanel': dict(),
         }

def remove_app_local_site(context):
    """
    This removes the site manager that previous listen versions
    installed at the physical root, then makes sure listen's
    IListLookup utility is installed at the portal level.
    """
    app = context.getPhysicalRoot()
    try:
        disableLocalSiteHook(app)
        logger.info('App root deactivated as a local site.')
    except TypeError:
        # we don't care if it's already not a site
        pass
    portal = getToolByName(context, 'portal_url').getPortalObject()
    setSite(portal)
    # clear out some muck that gets left behind  :-P
    sm = portal.getSiteManager()
    sm.adapters.__bases__ = (sm.adapters.__bases__[0],)
    sm.utilities.__bases__ = (sm.utilities.__bases__[0],)
    result = run_import_step(context, 'listen-various',
                             profile_id='listen:default',
                             )
    logger.info(result)


def rerun_import_steps(context):
    """
    Reimport any import steps that need to be reapplied to the site.

    Ideally, GenericSetup would provide a ZCML tag for this, but it's
    not there yet.
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

