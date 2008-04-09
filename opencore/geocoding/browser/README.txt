-*- mode: doctest ;-*-

Geocoding views of opencore content
===================================


Preferences view for Projects
------------------------------

    >>> self.login(project_admin)
    >>> projects = portal.projects
    >>> proj = projects[project_name]

Look for geolocation info, first when it's not set...

    >>> view = proj.restrictedTraverse('preferences')
    >>> form = {}
    >>> view.has_geocoder
    True
    >>> writer = get_geo_writer(view)
    >>> info, changed = writer.save_coords_from_form(form)
    >>> changed
    []
    >>> view.geo_info.get('position-latitude')
    ''
    >>> view.geo_info.get('position-longitude')
    ''


You can set and then view coordinates::

    >>> writer.set_geolocation((11.1, -22.2))
    True

    Clear the memoized stuff from the request to see the info.

    >>> utils.clear_all_memos(view)
    >>> print view.geo_info.get('position-latitude')
    11.1
    >>> print view.geo_info.get('position-longitude')
    -22.2

Calling again with the same points makes no change:

    >>> writer.set_geolocation((11.1, -22.2))
    False


You can extract stuff from the form::

    >>> form = {'position-latitude': '10.0', 'position-longitude': '-20.0'}
    >>> info, changed = writer.get_geo_info_from_form(form)
    >>> info['position-latitude'] == float(form['position-latitude'])
    True
    >>> info['position-longitude'] == float(form['position-longitude'])
    True

You can also pass in a string; if there's no coordinates passed, we
use a remote service to look them up.  We're using a mock so we don't
actually hit google on every test run::

    >>> utils.clear_status_messages(view)
    >>> form.clear()
    >>> form['position-text'] = "mock address"
    >>> form['location'] = 'mars'
    >>> info, changed = writer.save_coords_from_form(form)
    Called ....geocode('mock address')
    >>> utils.clear_all_memos(view)  # XXX ugh, wish this wasn't necessary.
    >>> print view.geo_info.get('position-latitude')
    12.0
    >>> print view.geo_info.get('position-longitude')
    -87.0

But we let the content's own form handlers handle everything else; we
might want to revisit this, it feels kind of schizo.  For now, this
means that other things in the request aren't saved unless we invoke
the form handler, not just the write wrapper.

    >>> view.geo_info['position-text'] == form['position-text']
    False
    >>> view.geo_info['location'] == form['location']
    False

We also now save the usual archetypes "location" field, for use as a
human-readable place name::

    >>> view = proj.restrictedTraverse('preferences')
    >>> utils.clear_status_messages(view)
    >>> view.request.form.update({'location': "oceania", 'update': True,
    ...     'project_title': 'IGNORANCE IS STRENGTH',
    ...     'position-text': 'mock address'})
    >>> view.handle_request()
    Called ....geocode('mock address')
    >>> utils.get_status_messages(view)
    [...u'The location has been changed.'...]
    >>> view.context.getLocation()
    'oceania'
    >>> utils.clear_all_memos(view)
    >>> view.geo_info.get('position-text')  # saved now.
    'mock address'

The view includes a bunch of convenient geo-related stuff for UIs::

    >>> sorted(view.geo_info.keys())
    ['is_geocoded', 'location', 'maps_script_url', 'position-latitude', 'position-longitude', 'position-text', 'static_img_url']
    >>> view.geo_info['is_geocoded']
    True
    >>> view.geo_info['location']
    'oceania'
    >>> round(view.geo_info['position-latitude'])
    12.0
    >>> round(view.geo_info['position-longitude'])
    -87.0
    >>> view.geo_info['position-text']
    'mock address'
    >>> view.geo_info['static_img_url']
    'http://maps.google.com/mapdata?latitude_e6=12000000&longitude_e6=4207967296&w=500&h=300&zm=9600&cc='

All-but-disabling this particular assertion for now, since it relies
on external configuration (should be mockable)::
    >>> view.geo_info['maps_script_url']
    '...'

We were really expecting http://maps.google.com/maps?file=api&v=2&key=...'


clean up...
    >>> view.request.form.clear()

Create view for Projects
------------------------

    >>> self.login(project_admin)
    >>> createview = projects.restrictedTraverse("create")
    >>> createview.request.form.update({'project_title': 'A geolocated project!',
    ...    'projid': 'testgeo', 'workflow_policy': 'medium_policy',
    ...    'position-latitude': '33.33', 'position-longitude': '44.44'})
    >>> out = createview.handle_request()
    >>> createview.errors
    {}
    >>> view = projects.restrictedTraverse('testgeo/preferences')
    >>> utils.clear_all_memos(view)
    >>> print view.geo_info['position-latitude']
    33.33
    >>> print view.geo_info['position-longitude']
    44.44

Clean that one up...

    >>> projects.manage_delObjects(['testgeo'])

##    "opencore.testing.utility.StubCabochonClient: args: ('testgeo',)"

    >>> view.request.form.clear()

XXX Add tests for publically available views of projects,
once they include geo info.


Feeds for Projects
------------------


These are all anonymously viewable::

    >>> self.logout()

The Projects collection can be adapted to a sequence of dictionaries
suitable for building a georss view::

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
    >>> info['id'] == project_name
    True
    >>> print info['geometry']['coordinates']
    (-87.0, 12.0, 0.0)
    >>> info['properties']['description']
    'No description'
    >>> info['properties']['link']
    'http://nohost/plone/projects/p3'
    >>> info['properties']['title']
    'IGNORANCE IS STRENGTH'

(Unfortunately it's hard to assert much about dates...  it should
look iso8601-ish.)

    >>> info['properties']['updated']
    '...-...-...T...:...:...'
    >>> info['properties']['created'] == info['properties']['created']
    True


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
    >>> info['id'] == project_name
    True
    >>> info['properties']['title']
    'IGNORANCE IS STRENGTH'

The projects georss view is exposed by a separate view that generates
xml.

    >>> feedview = projects.restrictedTraverse('@@georss')
    >>> xml = get_response_output(feedview)
    >>> lines = [s.strip() for s in xml.split('\n') if s.strip()]
    >>> print '\n'.join(lines)
    Status: 200 OK...
    <?xml...
    <feed
    ...xmlns="http://www.w3.org/2005/Atom"...
    <title>Projects</title>
    <link rel="self" href="http://nohost/plone/projects"/>...
    <entry>
    <title>IGNORANCE IS STRENGTH</title>...
    <id>http://nohost/plone/projects/p3</id>...
    <georss:where><gml:Point>
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



Profile edit views for Members
------------------------------

The view has a geo_info attribute containing pretty much everything
needed to build the UI::

    >>> people = portal.people
    >>> m1 = people.m1
    >>> self.login('m1')
    >>> view = m1.restrictedTraverse('@@profile-edit')
    >>> view.request.form.clear()
    >>> pprint(view.geo_info)
    {'is_geocoded': False,
     'location': '',
     'maps_script_url': '...',
     'position-latitude': '',
     'position-longitude': '',
     'position-text': '',
     'static_img_url': ''}

Submitting the form updates everything, and we get a static image url now::

    >>> view.request.form.update({'position-latitude': 45.0,
    ...  'position-longitude': 0.0, 'location': 'somewhere', })
    >>> redirected = view.handle_form()
    >>> view.request.form.clear()
    >>> view = m1.restrictedTraverse('@@profile-edit')
    >>> pprint(view.geo_info)
    {'is_geocoded': True,
     'location': 'somewhere',
     'maps_script_url': '...',
     'position-latitude': 45.0,
     'position-longitude': 0.0,
     'position-text': '',
     'static_img_url': 'http://...'}

Submitting the form with position-text should cause the (mock)
geocoder to be used::

    >>> view = m1.restrictedTraverse('@@profile-edit')
    >>> view.request.form.clear()
    >>> view.request.form.update({'position-text': 'atlantis',
    ...     'location': 'somewhere underwater', })
    ...
    >>> redirected = view.handle_form()
    Called ...geocode('atlantis')
    >>> utils.clear_all_memos(view)  # XXX Ugh, make this unnecessary.
    >>> pprint(view.geo_info)
    {'is_geocoded': True,
     'location': 'somewhere underwater',
     'maps_script_url': '...',
     'position-latitude': 12.0,
     'position-longitude': -87.0,
     'position-text': 'atlantis',
     'static_img_url': 'http://...'}


The public profile view should show the same data::

    >>> self.logout()
    >>> pview = m1.restrictedTraverse('@@profile')
    >>> pview.request.form.clear()
    >>> pview.geo_info == view.geo_info
    True


Feeds for Members
------------------

A bit of setup here to avoid depending on previous tests, yuck::

    >>> self.login('m1')
    >>> edit = m1.restrictedTraverse('profile-edit')
    >>> edit.request.form.clear()
    >>> edit.request.form.update({'location': 'nowhere', 'position-latitude': -66.0,
    ...      'position-longitude': 55.0})

    >>> redirected = edit.handle_form()


First try the views that generate info, should be public::

    >>> self.logout()
    >>> view = people.restrictedTraverse('@@geo')
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
      'properties': {...}}]
    >>> pprint(info[0]['properties'])
    {'created': '...-...-...T...:...:...',
     'description': 'No description',
     'language': '',
     'link': 'http://nohost/plone/people/m1',
     'location': 'nowhere',
     'title': 'Member One',
     'updated': '...-...-...T...:...:...'}


And similar info for generating kml::

    >>> info = list(view.forKML())
    >>> len(info)
    1
    >>> pprint(info)
    [{'coords_kml': '55.000000,-66.000000,0.000000',...


Now the actual georss xml feed::

    >>> feedview = portal.people.restrictedTraverse('@@georss')
    >>> xml = get_response_output(feedview)
    >>> lines = [s.strip() for s in xml.split('\n') if s.strip()]
    >>> print '\n'.join(lines)
    <?xml version="1.0"...
    <title>People</title>
    <link rel="self" href="http://nohost/plone/people"/>...
    <id>http://nohost/plone/people</id>
    <entry>
    <title>Member One</title>...
    <updated>...-...-...T...:...:...</updated>...
    <georss:where><gml:Point>
    <gml:pos>-66.000000 55.000000</gml:pos>
    </gml:Point>...


Now the actual kml feed::

    >>> feedview = portal.people.restrictedTraverse('@@kml')
    >>> xml = feedview()
    >>> lines = [s.strip() for s in xml.split('\n') if s.strip()]
    >>> print '\n'.join(lines)
    <?xml...
    <kml xmlns="http://earth.google.com/kml/2.1">
    <Document>...
    <name>People</name>...
    <Placemark>
    <name>Member One</name>
    <description>...
    <p>URL:
    <a href="http://nohost/plone/people/m1">http://nohost/plone/people/m1</a>...
    <Point>
    <coordinates>55.000000,-66.000000,0.000000</coordinates>
    </Point>...
    </kml>
