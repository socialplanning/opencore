==================
 opencore.project
==================

All things project: content, content views, listing views, various
subscribers, etc

    >>> import pdb; st = pdb.set_trace
    >>> projects = self.portal.projects

Default Project State
=====================

The layer runs opencore.project.handler.addredirection_hooks.  Let's
make sure the hooks are there::

    >>> from pprint import pprint
    >>> pprint([getattr(proj, '__before_traverse__', None) for proj in projects.objectValues()])
    [...,
     {(1, '__redirection_hook__'): <...AccessRule instance at ...>},
     {(1, '__redirection_hook__'): <...AccessRule instance at ...>},
     {(1, '__redirection_hook__'): <...AccessRule instance at ...>},
     {(1, '__redirection_hook__'): <...AccessRule instance at ...>...}]


Project Creation
================


    >>> from opencore.project.handler import handle_postcreation
    >>> request = self.app.REQUEST

Is done with a Fate addview.  This addview fires an event to handle
all the opencore specific manage_after* stuff.

By hand, this would look like so: first we would create project (we'll
check the state to prove there is no man behind the curtain)::

    >>> id_ = projects.invokeFactory("OpenProject", 'handroll')
    >>> handroll = getattr(projects, 'handroll')

# @@ why did policy config disappear
#    >>> handroll.objectIds()
#    ['.wf_policy_config']

    >>> hasattr(handroll, '__before_traverse__')
    False

    >>> handroll.getBRefs()
    []

    >>> handroll.title
    u''

we need to add some variables to the request, then we simulate firing
the event and check its state::

    >>> req_vars = dict(team_assignment=True,
    ...                 workflow_policy='open_policy',
    ...                 title="Handroll!",
    ...                 featurelets=['listen'],
    ...                 set_flets=True)
    >>> request.form.update(req_vars) 
    >>> handle_postcreation(AfterProjectAddedEvent(handroll, request))

Now we should have a redirection hook::

    >>> getattr(handroll, '__before_traverse__', None)
    {(1, '__redirection_hook__'): <...AccessRule instance at ...>}

We should refer to our team object::

    >>> handroll.getRefs()
    [<OpenTeam at /plone/portal_teams/handroll>]

Our title should be set::

    >>> handroll.title
    u'Handroll!'

And our project should contain a roster and list instance

    >>> ids = handroll.objectIds()
    >>> pprint(sorted(ids))
    ['.wf_policy_config', 'lists', 'project-home']

After creation is finished, our project shouldn't have any users
with the Owner role, because Owners get permissions regardless of
subsequent membership in the project::
    >>> handroll.users_with_local_role("Owner")
    []

When a subproject is created, we add an additional subscriber that
does 2 things: registers the redirect information and associates a
child project to its parent. To test, we will need to prep a project
as a parent::

    >>> parent = projects.p1
    >>> pinfo = redirect.activate(parent, "http://redirected") # note, no subprojects

    >>> from opencore.project.handler import handle_subproject_redirection
    >>> event = AfterSubProjectAddedEvent(handroll, projects.p1, request)
    >>> handle_subproject_redirection(event)
    >>> redirect.get_info(handroll).parent
    '/plone/projects/p1'

    >>> pinfo.values()
    ['/plone/projects/handroll']


Geolocation
============

Projects are marked as geolocatable.

    >>> from Products.PleiadesGeocoder.interfaces import IGeoreferenceable
    >>> IGeoreferenceable.providedBy(projects.p1)
    True

They're also marked as able to use Pleiades' default annotation adapter.

    >>> from Products.PleiadesGeocoder.interfaces import IGeoAnnotatableContent
    >>> IGeoAnnotatableContent.providedBy(proj)
    True

And marked as serializable.

    >>> from Products.PleiadesGeocoder.interfaces import IGeoserializable
    >>> IGeoserializable.providedBy(proj)
    True


They can be adapted to IGeoItemSimple, and coordinates set on them.
WARNING TO GEO NOOBS: This is an (x, y, z) point where x is longitude.
Yes, longitude goes first.

    >>> from Products.PleiadesGeocoder.interfaces import IGeoItemSimple
    >>> geo = IGeoItemSimple(projects.p1)
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
