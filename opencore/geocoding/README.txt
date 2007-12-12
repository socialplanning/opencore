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


Projects can be adapted to our IOCGeoView which provides a simple
API for everything we care about.

    >>> projects = self.portal.projects
    >>> proj = projects.p1
    >>> geo = proj.restrictedTraverse('oc-geo-info')
    >>> IOCGeoView.providedBy(geo)
    True
    >>> print geo.get_geolocation()
    None
    >>> geo.set_geolocation((1, 2))  # XXX lat first, change that?
    True
    >>> geo.get_geolocation()
    (2.0, 1.0, 0.0)
    >>> geo.set_geolocation((1, 2))  # same as before, so False.
    False
    >>> geo.geocode_from_form({'position-latitude': 5,
    ...                        'position-longitude': '6'})
    (5.0, 6.0)
    >>> geo.get_geolocation()  # geocode_from_form has no side effects.
    (2.0, 1.0, 0.0)


People
=======

People can be adapted to our OCGeoView which provides a simple API for
everything we care about.


    >>> m1folder = self.portal.people.m1
    >>> m1data = self.portal.portal_memberdata.m1
    >>> geo = self.portal.people.m1.restrictedTraverse('oc-geo-info')
    >>> IOCGeoView.providedBy(geo)
    True
    >>> print geo.get_geolocation()
    None
    >>> geo.set_geolocation((-3, -4))  # XXX lat first, change that?
    True
    >>> geo.get_geolocation()
    (-4.0, -3.0, 0.0)
    >>> geo.geocode_from_form({'position-latitude': 16,
    ...                        'position-longitude': '-44.0'})
    (16.0, -44.0)
    >>> geo.get_geolocation()  # geocode_from_form has no side effects.
    (-4.0, -3.0, 0.0)
