from zope.interface import implements
from zope.interface import Interface, Attribute

class IAfterProjectAddedEvent(Interface):
    """What happens after a project is added"""


class IAfterSubProjectAddedEvent(IAfterProjectAddedEvent):
    """What happens after a subproject is added"""
    

class AfterProjectAddedEvent(object):
    implements(IAfterProjectAddedEvent)
    def __init__(self, project, request):
        self.project = project
        self.request = request


class AfterSubProjectAddedEvent(AfterProjectAddedEvent):
    implements(IAfterSubProjectAddedEvent)

    def __init__(self, project, parent, request): 
        AfterProjectAddedEvent.__init__(self, project, request)
        self.parent = parent 
