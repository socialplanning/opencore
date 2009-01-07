"""
Script to ensure that all indexed project_ids are correct.
Fixes bad data related to http://trac.openplans.org/errors-openplans/ticket/36

This should be run after upgrading from opencore <= 0.13.0
to opencore >= 0.14.0.

"""

from Products.CMFCore.utils import getToolByName
from opencore.member import subscribers
from opencore.upgrades.utils import logger
import transaction


def fix_member_indexes(context, commit_batchsize=200):
    logger.info("Fixing membrane project_ids index")
    portal = getToolByName(context, 'portal_url').getPortalObject()
    mship_tool = getToolByName(portal, 'portal_membership')
    membrane_tool = getToolByName(portal, 'membrane_tool')
    fixed = 0
    brains = membrane_tool.unrestrictedSearchResults()
    total_count = len(brains)
    for i, brain in enumerate(brains):
        i += 1
        msg = "(%d out of %d)" % (i, total_count)
        try:
            mem = mship_tool.getMemberById(brain.getId)
        except AssertionError:
            logger.error('%s Got assertion error trying to find user %r, should not happen' % (msg, brain.getId()))
            continue
        if mem is None:
            logger.info("%s Got no member for id %r, should not happen" % (msg, brain.getId))
        elif set(mem.project_ids()) != set(brain.project_ids):
            # Don't want to reindex if I don't have to... our db is
            # bloated enough.
            subscribers.reindex_member_project_ids(mem, None)
            fixed += 1
            logger.info("%s *** FIXED %r" % (msg, brain.getId))
        else:
            logger.info("%s already ok: %r" % (msg, brain.getId))
        if fixed and (i % commit_batchsize == 0):
            transaction.get().note("reindexing members project_ids")
            transaction.commit()
            logger.info( "======= COMMITING =======================")
    
    logger.info( "Fixed %d out of %d total." % (fixed, total_count))
    if fixed:
        transaction.commit()
    else:
        transaction.abort()
        logger.info("Nothing to commit.")

