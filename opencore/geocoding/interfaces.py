from Products.PleiadesGeocoder.interfaces.simple import *
from zope.interface import Interface

class IReadGeo(Interface):
    """View for using OpenCore content with geocoding.
    """

    def get_geolocation():
        """Get the current coordinates of the context.
        Output as (longitude, latitude, z)"""

    def location_img_url():
        """
        Used for non-ajax UI to get a static map image for the context's
        location.
        """

    def is_geocoded():
        """Boolean. True if we can get coordinates, false otherwise.
        """

    def geo_info():
        """Returns a single dict containing all the interesting stuff.
        XXX more doc
        """

    def has_geocoder():
        """Boolean: Is a PleiadesGeocoder tool available?
        """
        
        


class IWriteGeo(Interface):

    def geocode_from_form(form=None):
        """Look up geocoding information as a (lat, lon) pair.

        The request (or optional passed-in mapping) should contain
        either 'position-latitude' and 'position-longitude' keys, or a
        'position-text' key that can be used to derive a latitude and
        longitude.  The latter takes precedence.

        If nothing works, returns None.
        """

    def set_geolocation(coords):
        """Store coordinates on the context (latitude first).
        If a change is made, return True; else return False.
        """
    
class IReadWriteGeo(IReadGeo, IWriteGeo):
    """both read + write.
    """
