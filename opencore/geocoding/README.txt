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


Projects can also be adapted to our 

The Projects collection can be adapted to a sequence of dictionaries
suitable for building a georss view.

    >>> view = projects.restrictedTraverse('@@geo')
    >>> info = list(view.forRSS())
    >>> len(info)
    1
    >>> info = info[0]

    Note that coords_georss is latitude-longitude, so you get them
    back in the reverse order:

    >>> info['coords_georss']
    '-20.000000 10.000000'
    >>> info['geometry']['type']
    'Point'
    >>> info['geometry']['coordinates']
    (10.0, -20.0, 0.0)
    >>> info['hasLineString']
    0
    >>> info['hasPoint']
    1
    >>> info['hasPolygon']
    0
    >>> info['id']
    'p1'
    >>> info['properties']['description']
    ''
    >>> info['properties']['link']
    'http://nohost/plone/projects/p1'
    >>> info['properties']['title']
    'Project One'

You can also adapt to a view suitable for building kml::

    >>> view = projects.restrictedTraverse('@@geo')
    >>> info = list(view.forKML())
    >>> len(info)
    1
    >>> info = info[0]

    Note that coords_kml is of the form longitude,latitude,z.

    >>> info['coords_kml']
    '10.000000,-20.000000,0.000000'
    >>> info['geometry']['type']
    'Point'
    >>> info['geometry']['coordinates']
    (10.0, -20.0, 0.0)
    >>> info['hasLineString']
    0
    >>> info['hasPoint']
    1
    >>> info['hasPolygon']
    0
    >>> info['id']
    'p1'


People
=======

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

So, we can now get a feed of geocoded people::

    >>> view = people.restrictedTraverse('@@geo')
    >>> info = list(view.forRSS())
    >>> len(info)
    1
    >>> pprint(info)
    [{'coords_georss': '2.000000 1.000000',
      'geometry': {'type': 'Point', 'coordinates': (1.0, 2.0, 0.0)},
      'hasLineString': 0,
      'hasPoint': 1,
      'hasPolygon': 0,
      'id': 'm1',
      'properties': {'description': 'No description',
                     'language': '',
                     'link': 'http://nohost/plone/people/m1',
                     'location': '',
                     'title': 'Member One'}}]


And for the kml feed::

    >>> info = list(view.forKML())
    >>> len(info)
    1
    >>> pprint(info)
    [{'coords_kml': '1.000000,2.000000,0.000000',...
    
