Geocoding views
================



Admin views for Projects
-------------------------


    >>> self.login(admin)
    >>> projects = portal.projects
    >>> proj = projects[projname]

Look for geolocation info, first when it's not set...

    >>> view = proj.restrictedTraverse('preferences')
    >>> form = {}
    >>> lat, lon = view.geocode_from_form(form)
    >>> view.set_geolocation(proj, lat, lon)
    False
    >>> view.project_info.has_key('position-latitude')
    False
    >>> view.project_info.has_key('position-longitude')
    False


You can set and then view coordinates::

    >>> view.set_geolocation(proj, 11.1, -22.2)
    True

    Clear the memoized stuff from the request to see the info.

    >>> utils.clear_all_memos(view)
    >>> print view.project_info.get('position-latitude')
    11.1
    >>> print view.project_info.get('position-longitude')
    -22.2

Calling again with the same points makes no change:

    >>> view.set_geolocation(proj, 11.1, -22.2)
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
    >>> print latlon
    (12.3456..., -87.6543...)
    >>> view.set_geolocation(proj, *latlon)
    True
    >>> utils.clear_all_memos(view)
    >>> print view.project_info.get('position-latitude')
    12.34567
    >>> print view.project_info.get('position-longitude')
    -87.654321


We also now save the usual archetypes "location" field, for use as a
human-readable place name::

    >>> view = proj.restrictedTraverse('preferences')
    >>> utils.clear_status_messages(view)
    >>> view.request.form.update({'location': "oceania", 'update': True,
    ...     'title': 'whatever'})
    >>> view.handle_request()
    >>> utils.get_status_messages(view)
    [...u'The location has been changed.'...]
    >>> view.context.getLocation()
    'oceania'

The non-ajaxy view defaults to using a google maps image based on the
current geolocation, by calling this method::

    >>> print view.location_img_url()
    http://maps.google.com/mapdata?latitude_e6=12345670&longitude_e6=4207312975&...


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


XXX Add tests for publically available views


Feeds
------

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
    <title>A geolocated project!</title>...
    <id>http://nohost/plone/projects/testgeo</id>...
    <gml:Point>
    <gml:pos>33.330000 44.440000</gml:pos>
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
    <name>A geolocated project!</name>
    <description>...
    <p>URL:
    <a href="http://nohost/plone/projects/testgeo">http://nohost/plone/projects/testgeo</a>...
    <Point>
    <coordinates>44.440000,33.330000,0.000000</coordinates>
    </Point>...
    </kml>


Clean up...

    >>> projects.manage_delObjects(['testgeo'])


Ditto for members::

    >>> self.login('m1')
    >>> m1 = portal.people.m1
    >>> geo = IGeoItemSimple(m1)
    >>> geo.setGeoInterface('Point', (55.0, -66.0, 0.0))
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
