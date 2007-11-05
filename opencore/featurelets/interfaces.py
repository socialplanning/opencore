from zope.interface import Interface

#BBB this module exists because the old pickled projects in the zodb expect them to be here
# new code imports them from their rightful location
# it was difficult to write a migration to move them out into their separate pacakges
# I encourage anybody that knows how, to do so
# there is some sample code (which doesn't work) for this in opencre.nui.setup

class IListenFeatureletInstalled(Interface):
    """marker for supporters with the listen featurelet installed"""

class ITaskTrackerFeatureletInstalled(Interface):
    """marker for supporters with the tasktracker featurelet installed"""

class IWordPressFeatureletInstalled(Interface):
    """marker for supporters with the wordpress featurelet installed"""

class IListenContainer(Interface):
    """marker interface to specify that a folder can support mailing lists"""
