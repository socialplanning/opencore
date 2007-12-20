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

class ReadGeoView(BrowserView):

    implements(interfaces.IReadGeo)

    def _geo(self):
        return IGeoItemSimple(self.context)

    def get_geolocation(self):
        """See IReadGeo. Note the output is ordered as (lon, lat, z)."""
        return self._geo().coords

    def location_img_url(self, width=500, height=300):
        """See IReadGeo."""
        geo = self._geo()
        if not geo.coords:
            return ''
        lon, lat, z = geo.coords
        # Don't know if order matters, so assume it does.
        params = (('latitude_e6', utils.google_e6_encode(lat)),
                  ('longitude_e6', utils.google_e6_encode(lon)),
                  ('w', width), ('h', height), # XXX These must match our css.
                  ('zm', 9600),  # Initial zoom.
                  ('cc', ''), # No idea what this is.
                  )
        url = 'http://maps.google.com/mapdata?' + urllib.urlencode(params)
        return url



class WriteGeoView(ReadGeoView):

    implements(interfaces.IWriteGeo)

    def set_geolocation(self, coords):
        """See IWriteGeo."""
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

    def geocode_from_form(self, form=None):
        """See IWriteGeo.

        If no values are provided, return an empty sequence.

        If position is provided but can't be geocoded, raise ValueError.

        If latitude or longitude values are provided but no good, raise the
        underlying ValueError or TypeError.
        """
        if form is None:
            form = self.request.form
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
                return lat, lon
            else:
                raise ValueError("Geocoding %r failed" % position)
        else:
            lon = form.get('position-longitude')
            lat = form.get('position-latitude')
            if lat is None or lon is None:
                return ()
            lon = float(lon)
            lat = float(lat)
            return (lat, lon)


class MemberareaReadGeoView(ReadGeoView, BaseView):

    # inheriting from BaseView is an excessive, lazy way to get at the
    # member. oh well.

    def _geo(self):
        return IGeoItemSimple(self.viewedmember())

class MemberareaWriteGeoView(WriteGeoView, ReadGeoView):
    pass


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
    # Use this to get a timestamp suitable for use in atom feeds.
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
