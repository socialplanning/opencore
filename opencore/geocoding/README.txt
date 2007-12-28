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
should be public::

    >>> self.logout()
    >>> projects = self.portal.projects
    >>> proj = projects.p1
    >>> view = ProjectBaseView(proj, proj.REQUEST)
    >>> view.request.form.clear()
    >>> reader = getReadGeoViewWrapper(view)
    >>> IReadGeo.providedBy(reader)
    True
    >>> print reader.get_geolocation()
    None
    >>> print reader.is_geocoded()
    False
    >>> reader.location_img_url()
    ''

The write interface should be restricted to project admins::

    >>> self.logout()
    >>> writer = getWriteGeoViewWrapper(view)
    >>> IWriteGeo.providedBy(writer)
    True
    >>> writer.geocode_from_form()
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'oc-geo-write' in this context
    >>> self.login('m1')
    >>> writer.geocode_from_form()
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'oc-geo-write' in this context
    >>> self.login('m3')
    >>> writer.geocode_from_form()
    False

Now let's use it::

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
    >>> writer.geocode_from_form({'position-latitude': 5,
    ...                           'position-longitude': '6'})
    (5.0, 6.0)
    >>> reader.get_geolocation()  # geocode_from_form has no side effects.
    (2.0, 1.0, 0.0)



People
=======

People can be adapted to our IReadGeo and IWriteGeo which provide a
simple API for everything we care about. The read interface should be
public::

    >>> self.logout()
    >>> m1folder = self.portal.people.m1
    >>> view = ProfileView(m1folder, m1folder.REQUEST)
    >>> view.request.form.clear()
    >>> reader = getReadGeoViewWrapper(view)
    >>> IReadGeo.providedBy(reader)
    True
    >>> print reader.get_geolocation()
    None
    >>> reader.location_img_url()
    ''

But not the write interface, It works only for the actual member::

    >>> m1data = self.portal.portal_memberdata.m1
    >>> writer = getWriteGeoViewWrapper(view)
    >>> IWriteGeo.providedBy(writer)
    True
    >>> writer.geocode_from_form()
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'oc-geo-write' in this context
    >>> self.login('m2')
    >>> writer.geocode_from_form()
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'oc-geo-write' in this context

    >>> self.login('m1')
    >>> writer.geocode_from_form()
    False

Now let's use it::

    >>> writer.set_geolocation((-3, -4))  # XXX lat first, change that?
    True
    >>> reader.get_geolocation()
    (-4.0, -3.0, 0.0)
    >>> writer.geocode_from_form({'position-latitude': 16,
    ...                           'position-longitude': '-44.0'})
    (16.0, -44.0)
    >>> reader.get_geolocation()  # geocode_from_form has no side effects.
    (-4.0, -3.0, 0.0)
    >>> reader.location_img_url()
    'http://...'
