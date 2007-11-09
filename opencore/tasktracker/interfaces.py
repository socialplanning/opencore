from zope.interface import Interface
from zope.schema import TextLine
from topp.featurelets.interfaces import IFeaturelet


class ITaskTrackerFeatureletInstalled(Interface):
    """
    Marks an object as having the task tracker featurelet installed.
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


class ITrackerFeaturelet(IFeaturelet):
    """
    a returner interface.  either returns actual featurelet or a proxy
    """
