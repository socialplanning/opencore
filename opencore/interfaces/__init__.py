#
try:
    from Products.OpenPlans.interfaces import IProject
    from Products.OpenPlans.interfaces import IAddProject, IEditProject
    from Products.OpenPlans.interfaces import IWriteWorkflowPolicySupport
    from Products.OpenPlans.interfaces import IReadWorkflowPolicySupport
except ImportError:
    from zope.interface import Interface
    class IProject(Interface):
        """dummy placeholder"""
