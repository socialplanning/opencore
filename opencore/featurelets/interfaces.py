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

class IWordpressFeatureletInstalled(Interface):
    """
    Marks an object as having the wordpress featurelet installed.
    """

class IWordpressContainer(Interface):
    """
    Marks an object as a wordpress container for the wordpress
    featurelet.
    """

from opencore.tasktracker.interfaces import *

