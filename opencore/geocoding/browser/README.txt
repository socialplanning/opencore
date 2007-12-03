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
    >>> view.update_geolocation(proj, lat, lon)
    False
    >>> view.project_info.has_key('position-latitude')
    False
    >>> view.project_info.has_key('position-longitude')
    False


You can set and then view coordinates::

    >>> view.update_geolocation(proj, 11.1, -22.2)
    True

    Clear the memoized stuff from the request to see the info.

    >>> utils.clear_all_memos(view)
    >>> print view.project_info.get('position-latitude')
    11.1
    >>> print view.project_info.get('position-longitude')
    -22.2

Calling again with the same points makes no change:

    >>> view.update_geolocation(proj, 11.1, -22.2)
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
    >>> view.update_geolocation(proj, *latlon)
    True
    >>> utils.clear_all_memos(view)
    >>> print view.project_info.get('position-latitude')
    12.34567
    >>> print view.project_info.get('position-longitude')
    -87.65432


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
    http://maps.google.com/mapdata?latitude_e6=12345670&longitude_e6=4207312976&...


Geolocation can also be set at project creation time::

    >>> createview = projects.restrictedTraverse("create")
    >>> createview.request.form.update({'title': 'a geolocated project!',
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

Clean up...

    >>> projects.manage_delObjects(['testgeo'])


XXX Add tests for publically available views
