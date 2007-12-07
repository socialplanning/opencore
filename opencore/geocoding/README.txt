GEOLOCATION
============

This package enhances opencore to allow storing and retrieving
geospatial coordinates, and getting georss feeds on containers.

Initially we're implementing this for the opencore people and projects
folders.


Projects
=========


    >>> projects = self.portal.projects
    >>> proj = projects.p1
    >>> from opencore.geocoding.interfaces import IGeoFolder, IOCGeoView, \
    ...    IGeoreferenceable, IGeoAnnotatableContent, IGeoserializable, \
    ...    IGeoserializableMembersFolder

Under the hood
--------------

    This is stuff that client code doesn't need to care about;
    we're just verifying that everything's wired up correctly.

    Projects are marked as geolocatable.

    >>> IGeoreferenceable.providedBy(proj)
    True

    They're also marked as able to use Pleiades' default annotation
    adapter, so we can mark them with geolocation info.

    >>> IGeoAnnotatableContent.providedBy(proj)
    True

    And marked as serializable.

    >>> IGeoserializable.providedBy(proj)
    True

    The projects folder is marked as a serializable container.

    >>> IGeoserializable.providedBy(projects)
    True
    >>> IGeoFolder.providedBy(projects)
    True


    Projects can be adapted to IGeoItemSimple, and coordinates set on them.
    WARNING TO GEO NOOBS: This is an (x, y, z) point where x is longitude.
    Yes, longitude goes first.

    >>> geo = IGeoItemSimple(proj)
    >>> print geo.coords
    None
    >>> coordinates = (10.0, -20.0, 0.0)
    >>> geo.setGeoInterface('Point', coordinates)
    >>> geo.coords
    (10.0, -20.0, 0.0)


API tests for projects
-----------------------

Projects can also be adapted to our IOCGeoView adapter which provides
a simple API for everything we care about.
XXX Duh, test this!


People
=======

Under the hood
---------------

   Client code doesn't need to care about any of this.
   This is a little more complex than I'd like due to the schism between
   member areas (people/foo) and member data (portal_memberdata/foo).

   The people folder is marked as a special folder interface.

    >>> people = self.portal.people
    >>> IGeoserializableMembersFolder.providedBy(people)
    True

    A member area is marked with the same interfaces as a project.

    >>> m1folder = self.portal.people.m1
    >>> IGeoserializable.providedBy(m1folder)
    True
    >>> IGeoreferenceable.providedBy(m1folder)
    True
    >>> IGeoAnnotatableContent.providedBy(m1folder)
    True

    The actual data is stored on the remember member::

    >>> m1data = self.portal.portal_memberdata.m1
    >>> IGeoAnnotatableContent.providedBy(m1data)
    True
    >>> IGeoreferenceable.providedBy(m1data)
    True

    You can get geo info on the people folder::

    >>> view = people.restrictedTraverse('@@geo')
    >>> view  # make sure our overrides.zcml took effect.
    <Products.Five.metaclass.GeoInfosetView object at ...>
    >>> info = list(view.forRSS())
    >>> len(info)
    0

    To see anything interesting, let's annotate a member and try again::

    >>> self.login('m1')
    >>> m1 = people.m1
    >>> geo = IGeoItemSimple(m1)
    >>> geo.setGeoInterface('Point', (1.0, 2.0, 0.0))
    >>> geo.coords
    (1.0, 2.0, 0.0)
    >>> geo.geom_type
    'Point'


API tests for people
--------------------

People can also be adapted to our IOCGeoView adapter which provides
a simple API for everything we care about.
XXX Duh, test this!

