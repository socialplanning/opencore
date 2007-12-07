Geocoding views of opencore content
===================================


Admin views for Projects
-------------------------


    >>> self.login(admin)
    >>> projects = portal.projects
    >>> proj = projects[projname]

Look for geolocation info, first when it's not set...

    >>> view = proj.restrictedTraverse('preferences')
    >>> form = {}
    >>> view.has_geocoder
    True
    >>> coords = view.geocode_from_form(form)
    >>> view.set_geolocation(proj, coords)
    False
    >>> view.project_info.has_key('position-latitude')
    False
    >>> view.project_info.has_key('position-longitude')
    False


You can set and then view coordinates::

    >>> view.set_geolocation(proj, (11.1, -22.2))
    True

    Clear the memoized stuff from the request to see the info.

    >>> utils.clear_all_memos(view)
    >>> print view.project_info.get('position-latitude')
    11.1
    >>> print view.project_info.get('position-longitude')
    -22.2

Calling again with the same points makes no change:

    >>> view.set_geolocation(proj, (11.1, -22.2))
    False


You can extract coordinates from the form::

    >>> form = {'position-latitude': '10.0', 'position-longitude': '-20.0'}
    >>> view.geocode_from_form(form)
    (10.0, -20.0)

You can also pass in a string which overrides the coordinates, and
uses a remote service to look them up.  Let's mock it so we don't
actually hit google on every test run::

    >>> utils.clear_status_messages(view)
    >>> text = "address does not matter for mock results"
    >>> form['position-text'] = text
    >>> latlon = view.geocode_from_form(form)
    Called ....geocode(
        'address does not matter for mock results')
    >>> latlon
    (12.0, -87.0)
    >>> view.set_geolocation(proj, latlon)
    True
    >>> utils.clear_all_memos(view)
    >>> print view.project_info.get('position-latitude')
    12.0
    >>> print view.project_info.get('position-longitude')
    -87.0


We also now save the usual archetypes "location" field, for use as a
human-readable place name::

    >>> view = proj.restrictedTraverse('preferences')
    >>> utils.clear_status_messages(view)
    >>> view.request.form.update({'location': "oceania", 'update': True,
    ...     'title': 'IGNORANCE IS STRENGTH'})
    >>> view.handle_request()
    >>> utils.get_status_messages(view)
    [...u'The location has been changed.'...]
    >>> view.context.getLocation()
    'oceania'

The non-ajaxy view defaults to using a google maps image based on the
current geolocation, by calling this method::

    >>> print view.location_img_url()
    http://maps.google.com/mapdata?latitude_e6=12000000&longitude_e6=42...


Geolocation can also be set at project creation time::

    >>> createview = projects.restrictedTraverse("create")
    >>> createview.request.form.update({'title': 'A geolocated project!',
    ...    'projid': 'testgeo', 'workflow_policy': 'medium_policy',
    ...    'position-latitude': '33.33', 'position-longitude': '44.44'})
    >>> out = createview.handle_request()
    >>> createview.errors
    {}
    >>> view = projects.restrictedTraverse('testgeo/preferences')
    >>> utils.clear_all_memos(view)
    >>> print view.project_info['position-latitude']
    33.33
    >>> print view.project_info['position-longitude']
    44.44

Clean that one up...

    >>> projects.manage_delObjects(['testgeo'])


XXX Add tests for publically available views of projects.


Feeds for Projects
------------------

The Projects collection can be adapted to a sequence of dictionaries
suitable for building a georss view.

    >>> view = projects.restrictedTraverse('@@geo')
    >>> info = list(view.forRSS())
    >>> len(info)
    1
    >>> info = info[0]  #XXX what order do they come back in?

    Note that coords_georss is latitude-longitude, so you get them
    back in the reverse order:

    >>> info['coords_georss']
    '12.000000 -87.000000'
    >>> info['geometry']['type']
    'Point'
    >>> info['geometry']['coordinates']
    (-87.0, 12.0, 0.0)
    >>> info['hasLineString']
    0
    >>> info['hasPoint']
    1
    >>> info['hasPolygon']
    0
    >>> info['id'] == projname
    True
    >>> print info['geometry']['coordinates']
    (-87.0, 12.0, 0.0)
    >>> info['properties']['description']
    ''
    >>> info['properties']['link']
    'http://nohost/plone/projects/p3'
    >>> info['properties']['title']
    'IGNORANCE IS STRENGTH'

You can also adapt to a view suitable for building kml::

    >>> view = projects.restrictedTraverse('@@geo')
    >>> info = list(view.forKML())
    >>> len(info)
    1
    >>> info = info[0]

    Note that coords_kml is of the form longitude,latitude,z.

    >>> info['coords_kml']
    '-87.000000,12.000000,0.000000'
    >>> info['geometry']['type']
    'Point'
    >>> print info['geometry']['coordinates']
    (-87.0, 12.0, 0.0)
    >>> info['hasLineString']
    0
    >>> info['hasPoint']
    1
    >>> info['hasPolygon']
    0
    >>> info['id'] == projname
    True
    >>> info['properties']['title']
    'IGNORANCE IS STRENGTH'


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
    <title>IGNORANCE IS STRENGTH</title>...
    <id>http://nohost/plone/projects/p3</id>...
    <gml:Point>
    <gml:pos>12.000000 -87.000000</gml:pos>
    </gml:Point>...


And a separate view that generates kml markup::

    >>> feedview = projects.restrictedTraverse('@@kml')
    >>> xml = feedview()
    >>> lines = [s.strip() for s in xml.split('\n') if s.strip()]
    >>> print '\n'.join(lines)
    <?xml...
    <kml xmlns="http://earth.google.com/kml/2.1">
    <Document>...
    <name>Projects</name>...
    <Placemark>
    <name>IGNORANCE IS STRENGTH</name>
    <description>...
    <p>URL:
    <a href="http://nohost/plone/projects/p3">http://nohost/plone/projects/p3</a>...
    <Point>
    <coordinates>-87.000000,12.000000,0.000000</coordinates>
    </Point>...
    </kml>




Admin views for Members
------------------------

XXX not implemented yet!

Feeds for Members
------------------

First try the views that generate info:

    >>> people = portal.people
    >>> view = people.restrictedTraverse('@@geo')
    >>> info = list(view.forRSS())
    >>> len(info)
    0
    >>> self.login('m1')
    >>> m1 = portal.people.m1
    >>> geo = IGeoItemSimple(m1)
    >>> geo.setGeoInterface('Point', (55.0, -66.0, 0.0))
    >>> info = list(view.forRSS())
    >>> len(info)
    1

    >>> pprint(info)
    [{'coords_georss': '-66.000000 55.000000',
      'geometry': {'type': 'Point', 'coordinates': (55.0, -66.0, 0.0)},
      'hasLineString': 0,
      'hasPoint': 1,
      'hasPolygon': 0,
      'id': 'm1',
      'properties': {'description': 'No description',
                     'language': '',
                     'link': 'http://nohost/plone/people/m1',
                     'location': '',
                     'title': 'Member One'}}]


And info for generating kml::

    >>> info = list(view.forKML())
    >>> len(info)
    1
    >>> pprint(info)
    [{'coords_kml': '55.000000,-66.000000,0.000000',...


Now the actual feeds::

    >>> feedview = portal.people.restrictedTraverse('@@georss')
    >>> xml = feedview()
    >>> lines = [s.strip() for s in xml.split('\n') if s.strip()]
    >>> print '\n'.join(lines)
    <?xml version="1.0"...
    <title>People</title>
    <link rel="self" href="http://nohost/plone/people"/>...
    <id>http://nohost/plone/people</id>
    <entry>
    <title>Member One</title>...
    <gml:Point>
    <gml:pos>-66.000000 55.000000</gml:pos>
    </gml:Point>...
