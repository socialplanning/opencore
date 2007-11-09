from zope.app.annotation import IAttributeAnnotatable

class IOpenMember(IAttributeAnnotatable):
    """
    Interface for OpenPlans members.

    A member class OpenMember already exists without implementing any
    z3 interfaces so this is presently just a marker interface. It may
    gain real content in the future but I want to tread very carefully
    so it will do nothing at first.
    """
    
