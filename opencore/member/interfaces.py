from zope.interface import Interface
from zope.app.annotation import IAttributeAnnotatable

class IOpenMember(IAttributeAnnotatable):
    """
    Interface for OpenPlans members.

    A member class OpenMember already exists without implementing any
    z3 interfaces so this is presently just a marker interface. It may
    gain real content in the future but I want to tread very carefully
    so it will do nothing at first.
    """

class IHandleMemberWorkflow(Interface):
    """
    Adapter for member objects to inquire about and set their state
    because I never remember how to use portal_workflow.
    """

    def is_unconfirmed(self):
        """
        Returns True if the user account associated with the member
        object is unconfirmed.
        """
    
    def confirm(self):
        """
        Confirms a user account. 

        No error checking is done within this method.
        """
