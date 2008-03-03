-*- mode: doctest ;-*-

GEOLOCATION
============

This package enhances opencore to allow storing and retrieving
geospatial coordinates, and getting georss feeds on containers.

Initially we're implementing this for the opencore people and projects
folders.

For tests of the underlying configuration that makes this all work,
see configuration.txt.


Projects
=========


Project views can be adapted to our IReadGeo and IWriteGeo which
provide a simple API for everything we care about.  The read interface
looks like this::

    >>> projects = self.portal.projects
    >>> proj = projects.p1
    >>> view = ProjectBaseView(proj, proj.REQUEST)
    >>> view.request.form.clear()
    >>> reader = get_geo_reader(view)
    >>> IReadGeo.providedBy(reader)
    True
    >>> print reader.get_geolocation()
    None
    >>> print reader.is_geocoded()
    False
    >>> reader.location_img_url()
    ''

Now let's try the writer::

    >>> self.login('m3')
    >>> view = ProjectBaseView(proj, proj.REQUEST)
    >>> view.request.form.clear()
    >>> writer = get_geo_writer(view)
    >>> IWriteGeo.providedBy(writer)
    True
    >>> info, changed = writer.get_geo_info_from_form()   # no change.
    >>> info == writer.geo_info()
    True
    >>> changed
    []

    >>> writer.set_geolocation((1, 2))  # XXX lat first, change that?
    True
    >>> reader.is_geocoded()
    True
    >>> reader.get_geolocation()
    (2.0, 1.0, 0.0)
    >>> reader.location_img_url()
    'http://maps.google.com/...'
    >>> writer.set_geolocation((1, 2))  # same as before, so False.
    False
    >>> info, changed = writer.get_geo_info_from_form({'position-latitude': 5,
    ...     'position-longitude': '6'})
    >>> print info['position-latitude'], info['position-longitude']
    5.0 6.0
    >>> reader.get_geolocation()  # get_geo_info_from_form has no side effects.
    (2.0, 1.0, 0.0)



The request overrides the values returned by get_geo_info_from_form,
but not geo_info:

    >>> old_info = view.geo_info.copy()
    >>> view.request.form.update({'location': 'nunya bizness',
    ...     'position-latitude': 1.2, 'position-longitude': 3.4,
    ...     'position-text': 'my house',  'static_img_url': 'IGNORED',
    ...     'maps_script_url': 'IGNORED'})
    >>> info, changed = writer.get_geo_info_from_form()
    >>> info == old_info
    False
    >>> info['location']
    'nunya bizness'
    >>> print info['position-latitude'], info['position-longitude']
    1.2 3.4
    >>> info['position-text']
    'my house'
    >>> info['static_img_url']
    'http://maps.google.com/mapdata?latitude_e6=1200000&longitude_e6=3400000&w=500&h=300&zm=9600&cc='
    >>> info['maps_script_url']
    '...'



People
=======

People can be adapted to our IReadGeo and IWriteGeo which provide a
simple API for everything we care about. First try the read
interface::

    >>> self.logout()
    >>> m1folder = self.portal.people.m1
    >>> view = ProfileView(m1folder, m1folder.REQUEST)
    >>> view.request.form.clear()
    >>> reader = get_geo_reader(view)
    >>> IReadGeo.providedBy(reader)
    True
    >>> print reader.get_geolocation()
    None
    >>> reader.location_img_url()
    ''

Now try the writer::

    >>> m1data = self.portal.portal_memberdata.m1
    >>> writer = get_geo_writer(view)
    >>> IWriteGeo.providedBy(writer)
    True
    >>> info, changed = writer.get_geo_info_from_form()
    >>> writer.geo_info() == info
    True
    >>> changed
    []
    >>> writer.set_geolocation((-3, -4))  # XXX lat first, change that?
    True
    >>> reader.get_geolocation()
    (-4.0, -3.0, 0.0)
    >>> info, changed = writer.get_geo_info_from_form({'position-latitude': 16,
    ...     'position-longitude': '-44.0'})
    >>> print info['position-latitude'], info['position-longitude']
    16.0 -44.0
    >>> reader.get_geolocation()  # the above has no side effects.
    (-4.0, -3.0, 0.0)
    >>> reader.location_img_url()
    'http://...'


Request values override get_geo_info_from_form but not geo_info:

    >>> old_info = view.geo_info.copy()
    >>> view.request.form.update({'position-latitude': 45.0,
    ...  'position-longitude': 0.0, 'location': 'somewhere', })

    >>> view.geo_info == old_info
    True
    >>> info, changed = writer.get_geo_info_from_form()
    >>> info == old_info
    False
    >>> sorted(changed)
    ['location', 'position-latitude', 'position-longitude', 'static_img_url']
    >>> pprint(info)
    {'is_geocoded': True,
     'location': 'somewhere',
     'maps_script_url': '...',
     'position-latitude': 45.0,
     'position-longitude': 0.0,
     'position-text': '',
     'static_img_url': 'http://maps...'}

If form has an updated position-text and not updated coords, we geocode
it and use the resulting coords::

    >>> view.request.form.clear()
    >>> form = old_info.copy()
    >>> form.update({'position-text': 'albania'})
    >>> info, changed = writer.get_geo_info_from_form(form)
    Called Products.PleiadesGeocoder....geocode('albania')
    >>> sorted(changed)
    ['position-latitude', 'position-longitude', 'position-text', 'static_img_url']
    >>> info['position-text']
    'albania'
    >>> print info['position-latitude'], info['position-longitude']
    12.0 -87.0
