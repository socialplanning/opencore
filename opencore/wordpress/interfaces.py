from zope.interface import Interface
from zope.schema import TextLine

class IWordPressFeatureletInstalled(Interface):
    """
    Marks an object as having the wordpress featurelet installed.
    """
