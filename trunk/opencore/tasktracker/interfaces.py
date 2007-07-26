from zope.interface import Interface, Attribute, implements
from zope.schema import TextLine, Bool

class ITaskTrackerFeatureletInstalled(Interface):
    """
    Marks an object as having the task tracker featurelet installed.
    """

class ITaskTrackerContainer(Interface):
    """
    Marks an object as a task tracker container
    """

class ITaskTrackerInfo(Interface):
    """utility declaratively representing the uri for a tasktracker
    instance"""
    uri = TextLine(
        title=u"Tasktracker URI", 
        description=u"Location of tasktracker",
        required=True)
    external_uri = TextLine(
        title=u"Tasktracker location",
        description=u"How to get to tasktracker externally",
        required=True)
