"""
$Id: __init__.py,v 1.2 2005/02/26 17:56:10 sidnei Exp $
"""

from zope.interface import Interface

class IReadWorkflowPolicySupport(Interface):
    """Interface for viewing information about customizable workflow
       policies on an object.
    """
    def getCurrentPolicyId():
        """Returns the current policy id or the default as determined by
           acquisition."""

    def getAvailablePolicies():
        """Returns a list of mappings representing available security
           policies, these contain an id, title, and description."""

class IWriteWorkflowPolicySupport(IReadWorkflowPolicySupport):
    """Interface for editing information about customizable workflow
       policies on an object.
    """
    def setPolicy(policy_in):
        """Sets the workflow policy on the object."""
