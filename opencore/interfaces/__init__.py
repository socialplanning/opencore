#
try:
    from Products.OpenPlans.interfaces import IProject
except ImportError:
    from zope.interface import Interface
    class IProject(Interface):
        """dummy placeholder"""
