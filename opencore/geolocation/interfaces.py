from zope.interface import Interface

class IGeoLocation(Interface):
    """provide geo location data"""

    # currently just store the latitude/longitude pair
    # in the future, we may expand this interface to include
    # more information, lke polygon outlines. We may also create
    # additional interfaces, and maybe even create a marker to specify
    # that an object provides geo locations

    def latitude_longitude(self):
        """return a latitude longitude pair as a tuple"""

    def store_latitude_longitude(self, lat_lon_pair):
        """store a latitude/longitude"""
