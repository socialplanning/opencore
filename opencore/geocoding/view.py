from Products.Five import BrowserView
from Products.PleiadesGeocoder.browser.info import get_coords
from Products.PleiadesGeocoder.interfaces import IGeoItemSimple
from opencore.browser.base import BaseView
import utils
from zope.interface import implements
import interfaces
import urllib

class OCGeoView(BrowserView):

    implements(interfaces.IOCGeoView)

    def _geo(self):
        return IGeoItemSimple(self.context)

    def update_geolocation(self, lat, lon):
        """See IOCGeoView."""
        # XXX what about non-Point locations?
        if lat is not None and lon is not None:
            geo = self._geo()
            # Longitude first! Yes, really.
            new_coords = (lon, lat, 0.0)
            if new_coords != geo.coords:
                geo.setGeoInterface('Point', new_coords)
                return True
        return False

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
        return IGeoItemSimple(self.member)

                        
class MemberFolderGeoItem:
    """ Adapt a member's home folder to IGeoItemSimple.
    """

    def __init__(self, context):
        self.context = context
        self.member = getattr(context.portal_memberdata, context.getId(), None)

    def setGeoInterface(self, geomtype, coords):
        # wtf is SRS anyway? cargo-culting it from PleiadesGeocoder.
        if not self.member:
            # XXX log something?
            return
        srs = 'EPSG:4326'
        geomtype = utils.serialize_geomtype(geomtype)
        coords = utils.serialize_coords(coords)
        self.member.setProperties(
            spatialCoordinates=coords, geometryType=geomtype, srs=srs)

    def isGeoreferenced(self):
        if not self.member:
            return False
        return bool(self.geom_type and self.coords)

    @property
    def coords(self):
        coords = self.member.getProperty('spatialCoordinates', '')
        geomtype = utils.serialize_geomtype(self.geom_type or 'Point')
        coords = get_coords(coords, geomtype)
        return coords

    @property
    def geom_type(self):
        gtype = self.member.getProperty('geometryType', None)
        if not gtype:
            return None
        try:
            return utils.deserialize_geomtype(gtype)
        except ValueError:
            return None

    @property
    def __geo_interface__(self):
        member = self.member
        folder = self.context
        # Kinda guessing what we want here.
        return {
            'id': folder.getId(),
            'properties': {
                'title': member.getFullname(),
                'description': member.getStatement(), # ?
                'link': folder.absolute_url(),
                },
            'geometry': {'type': self.geom_type, 'coordinates': self.coords}
            }
