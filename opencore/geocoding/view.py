from Products.PleiadesGeocoder.interfaces import IGeoItemSimple
from zope.interface import implements
from Products.Five import BrowserView
from utils import google_e6_encode
import interfaces
import urllib

class OCGeoView(BrowserView):

    implements(interfaces.IOCGeoView)

    def update_geolocation(self, lat, lon):
        """See IOCGeoView."""
        if lat is not None and lon is not None:
            geo = IGeoItemSimple(self.context)
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
        geo = IGeoItemSimple(self.context)
        if not geo.coords:
            return ''
        lon, lat, z = geo.coords
        # Don't know if order matters, so assume it does.
        params = (('latitude_e6', google_e6_encode(lat)),
                  ('longitude_e6', google_e6_encode(lon)),
                  ('w', 500), ('h', 300), # XXX These must match our css.
                  ('zm', 9600),  # Zoom.
                  ('cc', ''), # No idea what this is.
                  )
        url = 'http://maps.google.com/mapdata?' + urllib.urlencode(params)
        return url
