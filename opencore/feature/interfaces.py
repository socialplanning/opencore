from zope.interface import Interface
from zope import schema

class IFeature(Interface):
    """interface to represent a featured item"""

    title = schema.TextLine(title=u'Featured title', description=u'title of featured item')
    description = schema.Text(title=u'Featured description', description=u'description of featured item')
    link = schema.TextLine(title=u'Link to featured item', description=u'optional link to featured item')
    image_url = schema.TextLine(title=u'Url to feature image', description=u'optional url image of featured item')

class IProjectFeature(IFeature):
    """marker interface for project features specifically"""
