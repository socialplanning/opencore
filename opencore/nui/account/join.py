"""
separate pre-confirmed view for folks already invited to a project
"""
# @@ join should move in here too

from opencore.nui.account import accountview

class InviteJoinView(accountview):
    """a preconfirmed join view that also introspects any invitation a
    perspective member has"""
    
