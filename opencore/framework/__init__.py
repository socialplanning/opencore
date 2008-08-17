"""
until i think of a better place for this...
"""

from zope.interface import Interface

class IExtensibleContent(Interface):
    """
    a marker interface signalling that the object's
    behavior can be extended by plugins
    """
