from zope.interface import Interface
from topp.featurelets.interfaces import IFeaturelet


class ITaskTrackerFeatureletInstalled(Interface):
    """
    Marks an object as having the task tracker featurelet installed.
    """

class ITrackerFeaturelet(IFeaturelet):
    """
    a returner interface.  either returns actual featurelet or a proxy
    """
