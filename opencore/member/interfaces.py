from zope.interface import Interface
from zope.app.annotation import IAttributeAnnotatable
from zope.viewlet.interfaces import IViewletManager


class ICanHasRecentActivity(IViewletManager):
    """Viewlets for the recent activity section of the member profile."""

class IOpenMember(IAttributeAnnotatable):
    """
    Interface for OpenPlans members.

    A member class OpenMember already exists without implementing any
    z3 interfaces so this is presently just a marker interface. It may
    gain real content in the future but I want to tread very carefully
    so it will do nothing at first.
    """

class ICreateMembers(Interface):
    """
    Sort of a factory for member creation.

    Looks like it could be a multiadapter for requests, which means
    maybe it's actually just a view, but I'm going to start with what
    feels right here, which is ICreateMembers(portal).create(request.form)
    because it spells out what it's doing.
    """
    
    def validate(self, fields):
        """
        Validates fields for a member and returns an error dict
        """

    def create(self, fields):
        """
        Create and return a new member
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
