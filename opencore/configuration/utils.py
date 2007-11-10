"""
config utils
"""
from Products.CMFCore.utils import getToolByName


def product_config(variable, namespace, default=''):
    """
    get a variable from the product-config (etc/zope.conf)
    """
    from App import config
    
    try:
        cfg = config.getConfiguration().product_config.get(namespace)
    except AttributeError:
        from warnings import warn
        warn("""Product configuration most likely not loaded""")
        return default
        
    if cfg:
        return cfg.get(variable, default)
    return default



#
# This stuff should be in a config file, but we won't be using kupu
# for much longer, it's not worth the trouble
#
kupu_libraries = [
    dict(icon='string:${portal_url}/openproject_icon.png',
         id='projects',
         src='string:${portal/projects/absolute_url}/kupucollection.xml',
         title='string:Projects',
         uri='string:${portal/projects/absolute_url}'),

    dict(icon='string:${portal_url}/openproject_icon.png',
         id='current',
         src='string:${folder_url}/../kupucollection.xml',
         title='string:Current Folder',
         uri='string:${folder_url}/..'),
    
    dict(icon='string:${portal_url}/group.gif',
         id='people',
         title='string:People'),
    
    dict(icon='string:${portal_url}/kupuimages/confirm_icon.gif',
         id='myitems',
         src='string:${portal_url}/kupumyitems.xml',
         title='string:My items',
         uri='string:${portal_url}/kupumyitems.xml'),
    
    dict(icon='string:${portal_url}/kupuimages/confirm_icon.gif',
         id='recentitems',
         src='string:${portal_url}/kupurecentitems.xml',
         title='string:Recent',
         uri='string:${portal_url}/kupurecentitems.xml')]

kupu_resource_map = dict(linkable=('Document',
                              'Image',
                              'File',
                              'News Item',
                              'Event',
                              'PoiIssue',
                              'PoiResponse',
                              ),
                    mediaobject=('Image',),
                    collection=('Plone Site',
                                'Folder',
                                'OpenProject',
                                'Poitracker',
                                'Large Plone Folder'))
