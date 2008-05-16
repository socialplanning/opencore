from zope.component import adapter

from opencore.interfaces.event import IChangedTeamRolesEvent, ChangedTeamRolesEvent
from opencore.interfaces.membership import IOpenMembership

def membership_changed_reindex_catalog(mship, event):
    """when a membership role changes, we should reindex the catalog"""
    mship.reindexObject(idxs=['highestTeamRole'])
