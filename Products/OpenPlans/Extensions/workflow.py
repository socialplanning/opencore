"""
Module containing the external methods that are used as workflow
scripts for the various OpenCore workflows.  We use external methods
for all of our workflow scripts for ease of deployment and to avoid
the security headaches associated w/ TTW python scripts.
"""

def mship_visibility_changed(self, state_change):
    """
    Keep 'intended_visibility' value in sync w/ the wf state.
    """
    obj = state_change.object
    obj.intended_visibility = state_change.new_state.id

