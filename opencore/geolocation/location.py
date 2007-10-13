from zope.interface import implements
from zope.component import adapts
from zope.app.annotation.interfaces import IAnnotatable
from zope.app.annotation.interfaces import IAnnotations
from BTrees.OOBTree import OOBTree
from opencore.geolocation.interfaces import IGeoLocation

annot_key = 'opencore.geolocation.location'

class GeoLocation(object):
    adapts(IAnnotatable)
    implements(IGeoLocation)

    def __init__(self, context):
        self.context = context
        annot = IAnnotations(context)
        loc_annot = annot.get(annot_key, None)
        if loc_annot is None:
            loc_annot = OOBTree()
            annot[annot_key] = loc_annot
        self.annot = loc_annot

    def latitude_longitude(self):
        try:
            return self.annot['latlon']
        except KeyError:
            raise ValueError('No latitude, longitude')

    def store_latitude_longitude(self, lat_lon_pair):
        self.annot['latlon'] = lat_lon_pair
