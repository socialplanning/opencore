from Products.CMFCore.utils import getToolByName
from opencore.upgrades.utils import logger
import transaction

def retitle_member_areas(context):
    """
    change the title of the member areas on the site to use
    member id instead of member title, copied from `to_0_15_0` per
    http://www.openplans.org/projects/opencore/lists/opencore-dev/archive/2009/03/1236185295052

    Because the member folder's Title should not be exposed anywhere in the
    standard UI, this particular upgrade is non-critical; however, just to
    be on the safe side, you'll probably want to run it.

    The differences between this function and the 0.15 upgrade function it was
    cargoculted from are as follows:
     * It reverses that function for member folders. That is, in the 0.15 upgrade member folders
       were retitled to match their members' Title. Now we are reverting that and setting the
       title to match the member's id.
     * It does not touch member wiki home pages' Titles. Since that property can be changed
       through the UI by the member who owns the page, there's no reason to do it here.
    """

    portal = getToolByName(context, 'portal_url').getPortalObject()
    mdtool = getToolByName(portal, 'portal_memberdata')
    mem_ids = dict.fromkeys(
        mdtool.objectIds(spec='OpenMember'))

    i = 0
    changed = False
    for mem_id, home in portal.people.objectItems():
        if mem_id not in mem_ids:
            # what would this mean?
            continue
        i += 1
        member = mdtool._getOb(mem_id)
        mem_title = member.Title() or mem_id

        if home.Title() != mem_id:
            # This is not (or at least should not be) used anywhere in the standard UI, per #2779
            # It's not directly user-controllable, so we always do the upgrade
            changed = True
            home.setTitle(mem_id)
            home.reindexObject(idxs=['Title'])
            logger.info('retitled folder for %s' % mem_id)

        if changed and i % 400 == 0:
            transaction.commit()
            logger.info('===== COMMITTING (%d of %d) ====' %(i, len(mem_ids)))
            changed = False

    transaction.commit()
    logger.info('==== COMMITTING (%d of %d) ====' %(i, len(mem_ids)))
