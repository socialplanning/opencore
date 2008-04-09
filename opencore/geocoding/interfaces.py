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

    def get_geo_info_from_form(form=None, old_info=None):
        """
        Returns a dict and a list: (info, changed), Just like
        utils.update_info_from_form, but you don't have to pass
        anything if you have enough context.

        (You *can* optionally pass a form to override the
        request.form, and/or pass old_info if you're writing an add
        view and the content you're geocoding doesn't exist yet.)

        No side effects, just returns stuff.
        """

    def set_geolocation(coords):
        """Store coordinates on the context (latitude first).
        If a change is made, return True; else return False.
        """

    def save_coords_from_form(form=None):
        """Does a lookup just like get_geo_info_from_form,
        and saves the resulting coordinates
        if necessary."""

class IReadWriteGeo(IReadGeo, IWriteGeo):
    """both read + write.
    """
