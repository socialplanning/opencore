from zope.component import adapter

from opencore.interfaces.event import IChangedTeamRolesEvent, ChangedTeamRolesEvent

@adapter(IChangedTeamRolesEvent)
def membership_changed_reindex_catalog(event):
    """when a membership role changes, we should reindex the catalog"""
    mship = event.membership
    mship.reindexObject(idxs=['highestTeamRole'])
