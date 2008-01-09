from DateTime import DateTime
import urllib

def google_e6_encode(lat_or_lon):
    """Google makes life easy for themselves, and harder for us, by
    encoding signed float latitude and longitude into unsigned integers.

    >>> google_e6_encode(1)
    1000000
    >>> google_e6_encode(1.0)
    1000000
    >>> google_e6_encode(0)
    0
    >>> # Negatives get offset by 2 ** 32.
    >>> google_e6_encode(-1)
    4293967296
    >>> 2 ** 32 - google_e6_encode(-1)
    1000000
    >>> google_e6_encode(40.737562)
    40737562
    >>> google_e6_encode(-74.00709)
    4220960206
    """
    lat_or_lon *= 1000000
    if lat_or_lon < 0:
        lat_or_lon = 2 ** 32 + lat_or_lon
    return int(lat_or_lon)

def location_img_url(lat, lon, width=500, height=300):
    """
    Given latitude, longitude, and optional image size, return a URL
    to a static google maps image.

    >>> location_img_url(0, 0)
    'http://maps.google.com/mapdata?latitude_e6=0&longitude_e6=0&w=500&h=300&zm=9600&cc='

    You can pass width and height:
    >>> location_img_url(0, 0, 999, 77)
    'http://...&w=999&h=77&zm=9600&cc='

    """
    # Don't know if order matters to Google; assume it does.
    params = (('latitude_e6', google_e6_encode(lat)),
              ('longitude_e6', google_e6_encode(lon)),
              ('w', width), ('h', height), # XXX These must match our css.
              ('zm', 9600),  # Initial zoom.
              ('cc', ''), # No idea what this is.
              )
    url = 'http://maps.google.com/mapdata?' + urllib.urlencode(params)
    return url

def iso8601(dt_or_string=None):
    """
    Use this to get a timestamp suitable for use in atom feeds.
    Needed because Archetypes.ExtensibleMetadata date fields are sometimes
    DateTime objects, and sometimes strings. omg wtf etc.

    >>> iso8601('2007/01/01 01:00 GMT')
    '2007-01-01T01:00:00+00:00'

    >>> iso8601(DateTime('2001/01/01 12:00 PM EST'))
    '2001-01-01T12:00:00-05:00'

    With None or no args, you get 'now':
    >>> iso8601() == iso8601(None) == DateTime().ISO8601()
    True

    You get an error if the string can't be parsed:
    >>> iso8601('bogus!')
    Traceback (most recent call last):
    ...
    SyntaxError: bogus!

    """
    dt = DateTime(dt_or_string)
    return dt.ISO8601()
