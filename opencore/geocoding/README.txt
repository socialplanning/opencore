GEOLOCATION
============

Projects
=========


    >>> projects = self.portal.projects
    >>> proj = projects.p1
    >>> from Products.PleiadesGeocoder.interfaces import IGeoFolder, \
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

    >>> from Products.PleiadesGeocoder.interfaces import IGeoItemSimple
    >>> geo = IGeoItemSimple(proj)
    >>> print geo.coords
    None
    >>> coordinates = (10.0, -20.0, 0.0)
    >>> geo.setGeoInterface('Point', coordinates)
    >>> geo.coords
    (10.0, -20.0, 0.0)


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


The projects georss view is exposed by a separate view that generates
xml.

    >>> feedview = projects.restrictedTraverse('@@georss')
    >>> xml = feedview()
    >>> lines = [s.strip() for s in xml.split('\n') if s.strip()]
    >>> print '\n'.join(lines)
    <?xml...
    <feed xmlns="http://www.w3.org/2005/Atom"...
    <title>Projects</title>
    <link rel="self" href="http://nohost/plone/projects"/>...
    <entry>
    <title>Project One</title>...
    <id>http://nohost/plone/projects/p1</id>...
    <gml:Point>
    <gml:pos>-20.000000 10.000000</gml:pos>
    </gml:Point>...


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


And a separate view that generates kml markup::

    >>> feedview = projects.restrictedTraverse('@@kml')
    >>> xml = feedview()
    >>> lines = [s.strip() for s in xml.split('\n') if s.strip()]
    >>> print '\n'.join(lines)
    <?xml...
    <kml xmlns="http://earth.google.com/kml/2.1">
    <Document>...
    <name>Projects</name>
    ...
    <Placemark>
    <name>Project One</name>
    <description>
    ...
    <p>URL:
    <a href="http://nohost/plone/projects/p1">http://nohost/plone/projects/p1</a>
    ...
    <Point>
    <coordinates>10.000000,-20.000000,0.000000</coordinates>
    </Point>
    ...
    </kml>


People
=======


The people folder is marked as a special folder interface.

    >>> people = self.portal.people
    >>> IGeoserializableMembersFolder.providedBy(people)
    True


A member is marked with the same interfaces as a project.

    >>> m1 = people.m1
    >>> IGeoserializable.providedBy(m1)
    True
    >>> IGeoreferenceable.providedBy(m1)
    True
    >>> IGeoAnnotatableContent.providedBy(m1)
    True


You can get geo info on the people folder::

    >>> view = people.restrictedTraverse('@@geo')
    >>> info = list(view.forRSS())
    >>> len(info)
    0

To see anything interesting, let's annotate a member and try again::

XXX Left off here. PleiadesGeocoder treats members differently from
other content types; you apparently can't annotate them this same way.
Or you can, but a different view is used on the members folder, so it
doesn't notice these annotations.  Blah.  See the two view classes in
PleiadesGeocoder/browser/info.py ... the latter is used on the people
folder because P.G. marks that folder with IGeoserializableMembersFolder
at install time.  Disable that? or override their view?

    >>> geo = IGeoItemSimple(m1)
    >>> geo.setGeoInterface('Point', (1.0, 2.0, 0.0))
    >>> view = people.restrictedTraverse('@@geo')
    >>> info = list(view.forRSS())
    >>> import pprint
    >>> pprint.pprint(info)  # XXX empty, see above.
