from zope.interface import Interface
from zope.app.container.interfaces import IAdding

class IListenFeatureletInstalled(Interface):
    """
    Marks an object as having the listen featurelet installed.
    """

class IListenContainer(IAdding):
    """
    Marks an object as a mailing list container for the listen
    featurelet.
    """

class ITaskTrackerFeatureletInstalled(Interface):
    """
    Marks an object as having the task tracker featurelet installed.
    """

class ITaskTrackerContainer(Interface):
    """
    Marks an object as a task tracker container
    """
