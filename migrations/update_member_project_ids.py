"""
Script to ensure that all indexed project_ids are correct.
Fixes bad data related to http://trac.openplans.org/errors-openplans/ticket/36

This should be run after upgrading from opencore <= 0.13.0
to opencore >= 0.14.0.

"""

from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.SpecialUsers import system
from Products.CMFCore.utils import getToolByName
from Testing.makerequest import makerequest
from opencore.member import subscribers
import transaction

def fix_member_indexes(portal, commit_batchsize=200):
    mship_tool = getToolByName(portal, 'portal_membership')
    membrane_tool = getToolByName(portal, 'membrane_tool')

    fixed = 0
    brains = membrane_tool.unrestrictedSearchResults()
    total_count = len(brains)
    for i, brain in enumerate(brains):
        i += 1
        print "(%d out of %d)" % (i, total_count),
        mem = mship_tool.getMemberById(brain.getId)
        if mem is None:
            print "Got no member for id %r, should not happen" % brain.getId
        elif set(mem.project_ids()) != set(brain.project_ids):
            # Don't want to reindex if I don't have to... our db is
            # bloated enough.
            subscribers.reindex_member_project_ids(mem, None)
            fixed += 1
            print "*** FIXED %r" % brain.getId
        else:
            print " already ok: %r" % brain.getId
            
        if fixed and ((i % commit_batchsize == 0) or (i >= total_count)):
            transaction.get().note("reindexing members project_ids")
            transaction.commit()
            print "======= COMMITING ======================="
    print "Fixed %d out of %d total." % (fixed, total_count)
    if not fixed:
        print "Nothing to commit."



app=makerequest(app)
sm = getSecurityManager()
try:
    newSecurityManager(None, system)
    fix_member_indexes(app.openplans)
finally:
    setSecurityManager(sm)

