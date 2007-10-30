from zope.interface import Interface
from zope.schema import TextLine

class IWordPressFeatureletInstalled(Interface):
    """
    Marks an object as having the wordpress featurelet installed.
    """

class IWordPressInfo(Interface):
    """utility declaratively representing the uri for a wordpress
    instance"""
    uri = TextLine(
        title=u"Wordpress URI", 
        description=u"Location of wordpress",
        required=True)
    external_uri = TextLine(
        title=u"Wordpress location",
        description=u"How to get to wordpress externally",
        required=True)
