from DateTime import DateTime

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

def iso8601(dt_or_string):
    """
    Use this to get a timestamp suitable for use in atom feeds.
    Needed because Archetypes.ExtensibleMetadata date fields are sometimes
    DateTime objects, and sometimes strings. omg wtf etc.

    XXX test me
    """
    dt = DateTime(dt_or_string)
    return dt.ISO8601()
