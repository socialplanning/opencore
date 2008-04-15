"""Adapters to convert our content to interfaces that PleiadesGeocoder
can work with.
"""

from Products.CMFCore.utils import getToolByName
from Products.PleiadesGeocoder.geo import GeoItemSimple
from Products.PleiadesGeocoder.interfaces.simple import IGeoItemSimple
from opencore.member.interfaces import IOpenMember
from opencore.content.member import member_path
import utils

def MemberFolderGeoItem(context):
    """Factory to adapt a member's home folder to IGeoItemSimple.
    This allows us to treat remember members much the same as projects,
    which is simpler than the extra stuff PleiadesGeocoder has to do
    for normal Plone members.
    """
    member = getattr(context.portal_memberdata, context.getId(), None)
    if IOpenMember.providedBy(member):
        return IGeoItemSimple(member)
    return None
    
class MemberGeoItem(GeoItemSimple):

    @property
    def __geo_interface__(self):
        # Kinda guessing what info we want for members.
        member = self.context
        member_id = member.getId()
        # there's surely a better way to get this url.
        portal_url = getToolByName(member, 'portal_url')()
        home_url = '%s/%s' % (portal_url, member_path(member_id))
        properties = {
            'language': member.getProperty('language'),
            'location': member.getProperty('location'),
            # According to PleiadesGeocoder.browser.info comments,
            # OpenLayers can't handle an empty descr or title.
            'description': member.getProperty('description') or 'No description',
            'title': member.getProperty('fullname') or 'No title',
            'link': home_url,
            'updated': utils.iso8601(member.ModificationDate()),
            'created': utils.iso8601(member.CreationDate()),
            }
        
        return {
            'id': member_id,
            'properties': properties,
            'geometry': {'type': self.geom_type, 'coordinates': self.coords}
            }

class ProjectGeoItem(GeoItemSimple):

    @property
    def __geo_interface__(self):
        info = super(ProjectGeoItem, self).__geo_interface__
        project = self.context
        properties = {
            # According to PleiadesGeocoder.browser.info comments,
            # OpenLayers can't handle an empty descr or title.
            'description': info['properties']['description'] or 'No description',
            'title': info['properties']['title'] or 'No title',
            'updated': utils.iso8601(project.ModificationDate()),
            'created': utils.iso8601(project.CreationDate()),
            }
        info['properties'].update(properties)
        return info


class NullGeoItem:

    """used when we don't have a working adapter for the context.
    eg. the projects parent folder.
    """

    def __init__(self, context):
        self.__geo_interface__ = {}
        self.geom_type = ''
        self.coords = ()
    
    def setGeoInterface(self, *args, **kw):
        raise NotImplementedError

    def isGeoreferenced(self):
        return False
