from zope.interface import Interface

class IOCGeoView(Interface):
    """View for using OpenCore content with geocoding.
    """

    def update_geolocation(lat, lon):
        """Store a latitude and longitude on the context."""

    def geocode_from_form(form=None):
        """Return geocoding information as a (lat, lon) pair.

        The request (or optional passed-in mapping) should contain
        either 'position-latitude' and 'position-longitude' keys, or a
        'position-text' key that can be used to derive a latitude and
        longitude.  The latter takes precedence.

        If nothing works, returns None.
        """

    def location_img_url():
        """
        Used for non-ajax UI to get a static map image for the context's
        location.
        """
