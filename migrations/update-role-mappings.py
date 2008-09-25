"""
An alternate implementation of the workflow tool's updateRoleMappings
behaviour that commits the transaction frequently to prevent
inevitable conflict errors from such a long-running process.
"""

from Acquisition import aq_base

import transaction

from AccessControl.SecurityManagement import newSecurityManager
username = 'admin'
user = app.acl_users.getUser(username)
user = user.__of__(app.acl_users)
newSecurityManager(app, user)

from Testing.makerequest import makerequest
app=makerequest(app)

portal_id = 'openplans'
txn_commit_interval = 10 # num of obs btn txn commits

portal = app._getOb(portal_id)
wft = portal.portal_workflow

outer_count = 0
def _recursiveUpdateRoleMappings(ob, wfs):
    global outer_count
    count = 0
    wf_ids = wft.getChainFor(ob)
    if wf_ids:
        changed = 0
        for wf_id in wf_ids:
            wf = wfs.get(wf_id, None)
            if wf is not None:
                did = wf.updateRoleMappingsFor(ob)
                if did:
                    changed = 1
        if changed:
            count = count + 1
            outer_count = outer_count + 1
            if hasattr(aq_base(ob), 'reindexObject'):
                # Reindex security-related indexes
                try:
                    ob.reindexObject(idxs=['allowedRolesAndUsers'])
                except TypeError:
                    # Catch attempts to reindex portal_catalog.
                    pass
            if outer_count % txn_commit_interval == 0:
                transaction.get().note("Workflow Tool role mappings update: committed %d"
                                       % outer_count)
                transaction.commit()

    if hasattr(aq_base(ob), 'objectItems'):
        obs = ob.objectItems()
        if obs:
            for k, v in obs:
                changed = getattr(v, '_p_changed', 0)
                count = count + _recursiveUpdateRoleMappings(v, wfs)
                if changed is None:
                    # Re-ghostify.
                    v._p_deactivate()
    return count


wfs = {}
for id in wft.objectIds():
    wf = wft.getWorkflowById(id)
    if hasattr(aq_base(wf), 'updateRoleMappingsFor'):
        wfs[id] = wf
count = _recursiveUpdateRoleMappings(portal, wfs)

transaction.get().note("Workflow Tool role mappings update COMPLETE: %s"
                       % count)
transaction.commit()
print count
