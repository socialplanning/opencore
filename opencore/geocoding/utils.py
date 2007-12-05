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


def serialize_coords(values):
    """
    PleiadesGeocoder is kinda schizo about coordinates order.
    setGeoInterface() requires (longitude, latitude, z), but
    get_coords() requires a 'latitude longitude z' string.
    So we serialize to the latter format.

    Assumes len(values) is a multiple of 3, ignores extras.

    >>> serialize_coords((3.2, -9.0, 0.0))
    '-9.000000 3.200000 0.000000'
    >>> serialize_coords((1, 2, 3, 4, 5, 6, 999))
    '2.000000 1.000000 3.000000 5.000000 4.000000 6.000000'
    """
    # XXX there's probably a function like this in PleiadesGeocoder
    # but I haven't found it?

    nvalues = len(values)
    npoints = nvalues/3
    coords = []
    for i in range(npoints):
        coords.append('%f %f %f' % (values[3*i+1], values[3*i], values[3*i+2]))
    return ' '.join(coords)


def serialize_geomtype(geomtype):
    """
    Convert a geomtype to the storage representation.

    Ours is not to reason why, but PleiadesGeocoder uses
    one representations for geometry types as input & output,
    and a totally different representation for storage. WTF.

    >>> serialize_geomtype('Point')
    'point'
    >>> serialize_geomtype('blech')
    Traceback (most recent call last):
    ...
    ValueError: geometry type ... blech
    """
    geomtype = geomtype.strip()
    typemap = {'Point': 'point', 'LineString': 'line', 'Polygon': 'polygon'}
    output = typemap.get(geomtype)
    if output is None:
        raise ValueError("geometry type must be one of %s, not %s" %
                         (str(typemap.keys()), geomtype))
    return output

def deserialize_geomtype(geomtype):
    """Convert the internal storage representation to output.
    See serialize_geomtype for motivation.

    >>> deserialize_geomtype('point')
    'Point'
    >>> deserialize_geomtype('blah')
    Traceback (most recent call last):
    ...
    ValueError: geometry type ... blah
    """
    typemap = {'point': 'Point', 'line': 'LineString',  'polygon': 'Polygon'}
    output = typemap.get(geomtype)
    if output is None:
        raise ValueError("geometry type must be one of %s, not %s" %
                         (str(typemap.keys()), geomtype))
    return output

