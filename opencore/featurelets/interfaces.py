from zope.interface import Interface

class IListenFeatureletInstalled(Interface):
    """
    Marks an object as having the listen featurelet installed.
    """

class IListenContainer(Interface):
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
