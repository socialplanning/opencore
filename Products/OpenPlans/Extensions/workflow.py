"""
Module containing the external methods that are used as workflow
scripts for the various OpenCore workflows.  We use external methods
for all of our workflow scripts for ease of deployment and to avoid
the security headaches associated w/ TTW python scripts.
"""

from DateTime import DateTime

def mship_visibility_changed(self, state_change):
    """
    Keep 'intended_visibility' value in sync w/ the wf state.
    """
    obj = state_change.object
    obj.intended_visibility = state_change.new_state.id


def mship_activated(self, state_change):
    """
    Store the time the object was first activated
    """
    obj = state_change.object
    if getattr(obj, 'made_active_date', None):
        return
    obj.made_active_date = DateTime()
    obj.reindexObject()
    obj._p_changed = True
