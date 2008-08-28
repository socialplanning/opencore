-*- mode: doctest ;-*-

==================
 opencore.project
==================

All things project: content, content views, listing views, various
subscribers, etc

    >>> import pdb; st = pdb.set_trace
    >>> projects = self.portal.projects


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

