from DateTime import DateTime
from Products.Five import BrowserView
from Products.PleiadesGeocoder.browser.info import get_coords
from Products.PleiadesGeocoder.geo import GeoItemSimple
from Products.PleiadesGeocoder.interfaces.simple import IGeoItemSimple
from opencore.browser.base import BaseView
from opencore.content.member import member_path
from opencore.member.interfaces import IOpenMember
from zope.interface import implements
import interfaces
import urllib
import utils

class OCGeoView(BrowserView):

    implements(interfaces.IOCGeoView)

    def _geo(self):
        return IGeoItemSimple(self.context)

    def set_geolocation(self, coords):
        """See IOCGeoView."""
        if coords and not None in coords:
            geo = self._geo()
            # XXX need to handle things other than a point!
            lat, lon = coords[:2]
            # Longitude first! Yes, really.
            new_coords = (lon, lat, 0.0)
            if new_coords != geo.coords:
                geo.setGeoInterface('Point', new_coords)
                return True
        return False

    def get_geolocation(self):
        """See IOCGeoView. Note the output is ordered as (lon, lat, z)."""
        return self._geo().coords

    def geocode_from_form(self, form=None):
        """See IOCGeoView."""
        if form is None:
            form = self.request.form
        try:
            lon = float(form.get('position-longitude'))
            lat = float(form.get('position-latitude'))
        except TypeError:
            lon = lat = None
        except ValueError:
            lon = lat = None
        position = form.get('position-text', '').strip()
        if position:
            # If we got this, then presumably javascript was disabled;
            # it overrides the other form variables.
            # The value should be something we can look up via the geocoder.
            geo_tool = self.context.get_tool('portal_geocoder')
            records = geo_tool.geocode(position)
            if records:
                lat = records[0]['lat']
                lon = records[0]['lon']
            else:
                return None
        return lat, lon

    def location_img_url(self):
        """See IOCGeoView."""
        geo = self._geo()
        if not geo.coords:
            return ''
        lon, lat, z = geo.coords
        # Don't know if order matters, so assume it does.
        params = (('latitude_e6', utils.google_e6_encode(lat)),
                  ('longitude_e6', utils.google_e6_encode(lon)),
                  ('w', 500), ('h', 300), # XXX These must match our css.
                  ('zm', 9600),  # Initial zoom.
                  ('cc', ''), # No idea what this is.
                  )
        url = 'http://maps.google.com/mapdata?' + urllib.urlencode(params)
        return url


class OCMemberareaGeoView(OCGeoView, BaseView):

    # inheriting from BaseView is an excessive, lazy way to get at the
    # member. oh well.

    def _geo(self):
        return IGeoItemSimple(self.viewedmember())

def MemberFolderGeoItem(context):
    """Adapt a member's home folder to IGeoItemSimple.
    This allows us to treat remember members much the same as projects,
    which is simpler than the extra stuff PleiadesGeocoder has to do
    for normal Plone members.
    """
    member = getattr(context.portal_memberdata, context.getId(), None)
    if IOpenMember.providedBy(member):
        return IGeoItemSimple(member)
    return None


def _iso8601(dt_or_string):
    # Use this to get something suitable for use in atom feeds.
    # Needed because Archetypes.ExtensibleMetadata date fields are sometimes
    # DateTime objects, and sometimes strings. omg wtf etc.
    dt = DateTime(dt_or_string)
    return dt.ISO8601()
    
class MemberGeoItem(GeoItemSimple):

    @property
    def __geo_interface__(self):
        # Kinda guessing what info we want for members.
        member = self.context
        member_id = member.getId()
        # there's surely a better way to get this url.
        home_url = '%s/%s' % (member.portal_url(), member_path(member_id))
        properties = {
            'language': member.getProperty('language'),
            'location': member.getProperty('location'),
            # According to PleiadesGeocoder.browser.info comments,
            # OpenLayers can't handle an empty descr or title.
            'description': member.getProperty('description') or 'No description',
            'title': member.getProperty('fullname') or 'No title',
            'link': home_url,
            'updated': _iso8601(member.ModificationDate()),
            'created': _iso8601(member.CreationDate()),
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
            'updated': _iso8601(project.ModificationDate()),
            'created': _iso8601(project.CreationDate()),
            }
        info['properties'].update(properties)
        return info
