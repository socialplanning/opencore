from zope.interface import implements
from zope.interface import Interface, Attribute

class IAfterProjectAddedEvent(Interface):
    """What happens after a project is added"""


class IAfterSubProjectAddedEvent():
    """What happens after a subproject is added"""
    

class AfterProjectAddedEvent(object):
    implements(IAfterProjectAddedEvent)
    def __init__(self, project):
        self.project = project
        self.request = request


class AfterSubProjectAddedEvent(AfterProjectAddedEvent):
    implements(IAfterSubProjectAddedEvent)

