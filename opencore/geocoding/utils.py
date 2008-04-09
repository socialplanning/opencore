from DateTime import DateTime
from opencore.i18n import _
import logging
import urllib

logger = logging.getLogger('geocoding.utils')

def google_e6_encode(lat_or_lon):
    """Google makes life easy for themselves, and harder for us, by
    encoding signed float latitude and longitude into unsigned integers.

    >>> google_e6_encode(1)
    '1000000'
    >>> google_e6_encode(1.0)
    '1000000'
    >>> google_e6_encode(0)
    '0'
    >>> # Negatives get offset by 2 ** 32.
    >>> google_e6_encode(-1)
    '4293967296'
    >>> str(2 ** 32 - int(google_e6_encode(-1)))
    '1000000'
    >>> google_e6_encode(40.737562)
    '40737562'
    >>> google_e6_encode(-74.00709)
    '4220960206'
    """
    lat_or_lon *= 1000000
    if lat_or_lon < 0:
        lat_or_lon = 2 ** 32 + lat_or_lon
    return str(int(lat_or_lon))

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

    It should work on dates in any timezone, regardless of the local zone::

    >>> iso8601(DateTime('2001/01/01 12:00 PM EST'))
    '2001-01-01T12:00:00-05:00'
    >>> iso8601(DateTime('2001/01/01 12:00 PM PST'))
    '2001-01-01T12:00:00-08:00'

    With None or no args, you get 'now':
    >>> iso8601() == iso8601(None) == DateTime().ISO8601()
    True

    You get an error if the string can't be parsed:
    >>> iso8601('bogus!')
    Traceback (most recent call last):
    ...
    SyntaxError: bogus!

    """
    if isinstance(dt_or_string, DateTime):
        # we have to care because of a zope bug, see
        # https://bugs.launchpad.net/zope2/+bug/200007
        dt = dt_or_string
    else:
        dt = DateTime(dt_or_string)
    return dt.ISO8601()


def update_info_from_form(orig_info, form, geocoder):
    """Given a dict of old geo info, a form dictionary, and a geocoder
    to use if needed, returns a dict and a list: (new_info, changed).

    The new_info dict is just like the orig_info input, but merged
    with any changes from the form, and does geocoding to get new
    coords if necessary.

    The changed list is a list of keys in the dict that are different
    from the values in orig_info.

    The geocoder must have a 'geocode' method that accepts a string
    argument and returns a list of list results.  If geocoding fails,
    we'll add an 'errors' key to the result dict, with a message.

    A bit of test setup::

    >>> orig = {'position-latitude': '', 'position-longitude': '',
    ...         'position-text': 'ocean south of ghana',
    ...         'location': 'very mysterious',
    ...         'static_img_url': ''}
    >>> from opencore.geocoding.testing import MockGeocoder
    >>> geocoder = MockGeocoder()
    >>> from pprint import pprint

    If empty form is passed, nothing changes::
    >>> info, changed = update_info_from_form(orig, {}, geocoder)
    >>> info == orig
    True
    >>> changed
    []

    If only text is passed, we use that for geocoding::

    >>> form = {'position-text': 'aha'}
    >>> info, changed = update_info_from_form(orig, form, geocoder)
    Called Products.PleiadesGeocoder.geocode.Geocoder.geocode()
    >>> info == orig
    False
    >>> sorted(changed)
    ['position-latitude', 'position-longitude', 'position-text', 'static_img_url']
    >>> print info['position-latitude']
    12.0
    >>> print info['position-longitude']
    -87.0
    >>> print info['static_img_url']
    http://maps.google...

    If coordinates are passed, we use those instead. But you must pass both
    or nothing happens::

    >>> form = {'position-latitude': 5}
    >>> info, changed = update_info_from_form(orig, form, geocoder)
    >>> info == orig
    True
    >>> changed
    []
    >>> form['position-longitude'] = 6
    >>> info, changed = update_info_from_form(orig, form, geocoder)
    >>> info == orig
    False
    >>> info['position-latitude'] == form['position-latitude']
    True
    >>> info['position-longitude'] == form['position-longitude']
    True
    >>> sorted(changed)
    ['position-latitude', 'position-longitude', 'static_img_url']

    If text is passed but we get no results from the geocoder, we use
    the old coordinates and put an errors dict in the 'errors'
    key. This looks weird but it's convenient for our views::

    >>> geocoder = MockGeocoder(returnval=[])
    >>> form = {'position-text': 'blah'}
    >>> info, changed = update_info_from_form(orig, form, geocoder)
    Called Products.PleiadesGeocoder.geocode.Geocoder.geocode()
    >>> info['errors']
    {'position-text': u'psm_geocode_failed'}
    >>> changed
    ['errors']

    If coordinates *and* text are passed, we use the coords::

    >>> form = {'position-latitude': 8, 'position-longitude': 9,
    ...         'position-text': 'stored but not used for geocoding'}
    >>> info, changed = update_info_from_form(orig, form, geocoder)
    >>> info['position-text'] == form['position-text']
    True
    >>> info['position-latitude'] == form['position-latitude']
    True
    >>> info['position-longitude'] == form['position-longitude']
    True
    >>> sorted(changed)
    ['position-latitude', 'position-longitude', 'position-text', 'static_img_url']


    """

    orig_info = orig_info.copy()
    new_info = orig_info.copy()
    oldlat = orig_info.get('position-latitude', '')
    newlat = form.get('position-latitude', '')

    oldlon = orig_info.get('position-longitude', '')
    newlon = form.get('position-longitude', '')

    oldtext = orig_info.get('position-text', '')
    newtext = form.get('position-text', '')

    oldloc = orig_info.get('location', '')
    newloc = form.get('location', '')

    if newloc and newloc != oldloc:
        new_info['location'] = newloc
    if newtext and newtext != oldtext:
        new_info['position-text'] = newtext

    if (newlat != '' and newlon != '') and (newlat != oldlat or
                                            newlon != oldlon):
        # If form has updated coords, always use them.
        try:
            newlat = float(newlat)
            newlon = float(newlon)
        except (TypeError, ValueError):
            logger.error(
                "bad values for lat & lon? got %s" % str(newlat, newlon))
        else:
            new_info['position-latitude'] = newlat
            new_info['position-longitude'] = newlon
            new_info['static_img_url'] = location_img_url(newlat, newlon)
    elif newtext and newtext != oldtext:
        # If form has an updated position-text and NOT updated coords,
        # geocode it and use the resulting coords.
        records = geocoder.geocode(newtext)
        if records:
            newlat, newlon = (records[0]['lat'], records[0]['lon'])
            new_info['position-latitude'] = newlat
            new_info['position-longitude'] = newlon
            new_info['static_img_url'] = location_img_url(newlat, newlon)
        else:
            new_info['errors'] = {
                'position-text': _(
                u'psm_geocode_failed',
                u"Sorry, we were unable to find that address on the map.")}
            new_info['position-text'] = oldtext
    changed = []
    for key in new_info.keys():
        if new_info[key] != orig_info.get(key):
            changed.append(key)
    return new_info, changed
