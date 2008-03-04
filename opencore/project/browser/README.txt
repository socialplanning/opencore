-*- mode: doctest ;-*-

======================
 opencore.project.browser
======================

Add view
========

The add view is restricted to authenticated members:

    >>> projects = self.portal.projects
    >>> self.logout()
    >>> view = projects.restrictedTraverse("create")
    Traceback (innermost last):
    ...
    Unauthorized: ...

    >>> self.login('test_user_1_')
    >>> view = projects.restrictedTraverse("create")
    >>> view
    <Products.Five.metaclass.ProjectAddView object at...>

    >>> form_vars = dict(projid='test1', __initialize_project__=True,
    ...                  workflow_policy='medium_policy',
    ...                  add=True)
    >>> view.request.form.update(form_vars)

The test setup should be ensuring that geocoding is disabled::

    >>> view.has_geocoder
    False

Looking up geo info on the add view gives us nothing much useful,
because the project doesn't exist yet::

    >>> view.geo_info['is_geocoded']
    False
    
Try setting some invalid titles::
    >>> view.request.form['project_title'] = ""
    >>> out = view.handle_request()
    >>> view.errors
    {'project_title': 'The project name must contain at least 2 characters with at least 1 letter or number.'}
    >>> view.errors = {}

    >>> view.request.form['project_title'] = "1"
    >>> out = view.handle_request()
    >>> view.errors
    {'project_title': 'The project name must contain at least 2 characters with at least 1 letter or number.'}
    >>> view.errors = {}

    >>> view.request.form['project_title'] = "!@#$%"
    >>> out = view.handle_request()
    >>> view.errors
    {'project_title': 'The project name must contain at least 2 characters with at least 1 letter or number.'}
    >>> view.errors = {}

How about an invalid id?::
    >>> view.request.form['project_title'] = "valid title"
    >>> view.request.form['projid'] = ''
    >>> out = view.handle_request()
    >>> view.errors
    {'id': 'The project url may contain only letters, numbers, hyphens, or underscores and must have at least 1 letter or number.'}
    >>> view.errors = {}

And, another invalid id::
    >>> view.request.form['projid'] = 'abcd1-_+'
    >>> out = view.handle_request()
    >>> view.errors
    {'id': 'The project url may contain only letters, numbers, hyphens, or underscores and must have at least 1 letter or number.'}
    >>> view.errors = {}

And an id with a reserved name also produces an error::
    >>> view.request.form['projid'] = 'summary'
    >>> out = view.handle_request()
    >>> view.errors
    {'id': 'Name reserved'}
    >>> view.errors = {}

Now, a valid title and id::
    >>> view.request.form['project_title'] = 'now a valid title!'
    >>> view.request.form['projid'] = 'test1'
    >>> out = view.handle_request()
    >>> view.errors
    {}
    >>> proj = projects.test1
    >>> proj
    <OpenProject at /plone/projects/test1>

And let's check that the project title and id are properly set
    >>> proj.title
    u'now a valid title!'
    >>> proj.id
    'test1'

Let's verify that the last modified author was properly set
    >>> from opencore.interfaces.catalog import ILastModifiedAuthorId
    >>> ILastModifiedAuthorId(proj)
    'test_user_1_'

And if we login as a different user, it should stil be the same
    >>> self.logout()
    >>> self.login('m1')
    >>> ILastModifiedAuthorId(proj)
    'test_user_1_'

Log back in as the test user
    >>> self.logout()
    >>> self.login('m2')

Can the creator of a closed project really leave? Let's find out
in a test::
    >>> projects = self.portal.projects
    >>> view = projects.restrictedTraverse("create")
    >>> form_vars = dict(projid='test1', __initialize_project__=True,
    ...                  workflow_policy='closed_policy',
    ...                  add=True)
    >>> view.request.form.update(form_vars)
    >>> view.request.form['project_title'] = 'testing 1341'
    >>> view.request.form['projid'] = 'test1341'
    >>> out = view.handle_request()
    >>> proj = projects.test1341
    >>> self.logout()

Make sure a nonmember of this new closed project can't access it::
    >>> self.login('m1')
    >>> view = projects.test1341.restrictedTraverse("preferences")
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'preferences' in this context
    >>> self.logout()

Log back in as the creator and deactivate him; now he can't access
views on his project either::
    >>> self.login('m2')
    >>> view = projects.test1341.restrictedTraverse("manage-team")
    >>> wftool = view.get_tool("portal_workflow")
    >>> team = view.team
    >>> mship = team._getOb("m2")
    >>> wftool.doActionFor(mship, "deactivate")

    >>> view = projects.test1341.restrictedTraverse("preferences")
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'preferences' in this context

Make sure he can't access wiki pages in his project, too::
    >>> view = projects.test1341.restrictedTraverse("project-home")
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'project-home' in this context

    >>> self.logout()
    >>> self.login('test_user_1_')

Maps url should work if the geocoder is available::

    >>> view = projects.restrictedTraverse('create')
    >>> view.has_geocoder = True

    
Preference View
===============

    >>> proj = projects.test1
    >>> proj.restrictedTraverse('preferences')
    <...SimpleViewClass ...preferences...>

    >>> view = proj.restrictedTraverse('preferences')
    >>> view.project_info['security']
    'medium_policy'

    Remove all featurelets

    The test setup should have disabled geocoding::

    >>> view = proj.restrictedTraverse('preferences')
    >>> view.has_geocoder
    False

    >>> form_vars = dict(workflow_policy='closed_policy',
    ...                  update=True,
    ...                  featurelets=[],
    ...                  set_flets=1,
    ...                  __initialize_project__=False,
    ...                  )

    >>> view.request.form.update(form_vars)

    For some reason, we need this in here
    And it doesn't like it if we set it on request.form
    >>> view.request.set('flet_recurse_flag', None)

Try setting a bogus title::
    >>> view.request.form['project_title'] = '?'
    >>> out = view.handle_request()
    >>> view.errors
    {'project_title': u'err_project_name'}
    >>> view.errors = {}

Clear old PSMs

    >>> utils.clear_status_messages(view)


Now set a valid title::
    >>> view.request.form['project_title'] = 'new full name'
    >>> view.handle_request()
    >>> utils.get_status_messages(view)
    [u'The security policy has been changed.', u'The title has been changed.']

    >>> view.errors
    {}
    >>> view = proj.restrictedTraverse('preferences')

    >>> proj.Title()
    'new full name'
    >>> proj.title
    u'new full name'
    >>> proj.getFull_name()
    'new full name'

    >>> IReadWorkflowPolicySupport(proj).getCurrentPolicyId()
    'closed_policy'

    >>> from opencore.project.utils import get_featurelets
    >>> get_featurelets(proj)
    []

#re-add mailing lists
    >>> utils.clear_status_messages(view)
    >>> view.request.set('flet_recurse_flag', None)
    >>> view.request.form['featurelets'] = ['listen']
    >>> view.handle_request()
    >>> utils.get_status_messages(view)
    [u'Mailing lists feature has been added.']


Make sure we can install a TaskTracker featurelet too::
    >>> form_vars = dict(title='new full name',
    ...                  workflow_policy='closed_policy',
    ...                  update=True,
    ...                  featurelets=['tasks'],
    ...                  set_flets=1,
    ...                  __initialize_project__=False)
    >>> view.request.set('flet_recurse_flag', None)
    >>> view.request.form.update(form_vars)
    >>> view.handle_request()
    Called ...
    >>> get_featurelets(proj)
    [{'url': 'tasks', 'name': 'tasks', 'title': u'Tasks'}]

    Verify who we are logged in as
    >>> getToolByName(self.portal, 'portal_membership').getAuthenticatedMember().getId()
    'test_user_1_'

    Verify that if we try to access a closed project as an anonymous
    user, we lose
    >>> self.logout()
    >>> proj.restrictedTraverse('preferences')
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'preferences' in this context

    We should also not be able to edit the default page
    >>> page_id = 'project-home'
    >>> page = getattr(proj, page_id)
    >>> page.restrictedTraverse('edit')
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'edit' in this context

    Log back in as the right user
    >>> self.login('test_user_1_')

    Now we can see it again
    >>> proj.restrictedTraverse('preferences')
    <...SimpleViewClass ...preferences...>


If the geocoding tool is not available, these methods successfully do
nothing interesting::

    >>> view.has_geocoder
    False
    >>> pprint(view.geo_info)
    {'is_geocoded': False,
     'location': '',
     'maps_script_url': '',
     'position-latitude': '',
     'position-longitude': '',
     'position-text': '',
     'static_img_url': ''}



Team view
=========

Set up the view::

    >>> from opencore.project.browser.team import ProjectTeamView
    >>> request = self.portal.REQUEST
    >>> proj = projects.p1
    >>> view = ProjectTeamView(proj, request)

Sort by username::

    >>> results = view.memberships('username')
    >>> brains = list(results)
    >>> len(brains)
    3
    >>> [b.getId for b in brains]
    ['m1', 'm3', 'm4']

Clear the memoize from the request::

    >>> utils.clear_all_memos(view)

Sorting by nothing should sort by username::

    >>> results = view.memberships(None)
    >>> brains = list(results)
    >>> len(brains)
    3
    >>> [b.getId for b in brains]
    ['m1', 'm3', 'm4']

Clear the memoize from the request::

    >>> utils.clear_all_memos(view)

Now try sorting by location::
First however, we have to give some members locations
    >>> for mem_id, location in zip(['m1', 'm4', 'm3'], ['ny', 'ny', 'FL']):
    ...     mem = getattr(self.portal.portal_memberdata, mem_id)
    ...     mem.location = location
    ...     mem.reindexObject(idxs=['getLocation'])
    >>> results = view.memberships('location')
    >>> brains = list(results)
    >>> len(brains)
    3

Verify that the locations were set
    >>> for b in brains: assert b.getLocation

They should be sorted according to id, by location
    >>> [b.getId for b in brains]
    ['m3', 'm1', 'm4']

Test the projects for members work::
    >>> mem = self.portal.portal_memberdata.m4
    >>> mem_projects = view.projects_for_member(mem)
    >>> mem_proj_ids = [mem_project.getId() for mem_project in mem_projects]
    >>> mem_proj_ids.sort()
    >>> mem_proj_ids
    ['p1', 'p2', 'p4']
    >>> view.num_projects_for_member(brains[0].getObject())
    3

Clear the memoize from the request::

    >>> utils.clear_all_memos(view)

Let's sort based on the membership date::

    >>> results = view.memberships('membership_date')
    >>> mem_brains = list(results)
    >>> len(mem_brains)
    3

We need to get the corresponding membership brains to verify if they are in
the correct order::

    >>> mship_brains = view.catalog(path='/plone/portal_teams/p1',
    ...                             portal_type='OpenMembership',
    ...                             getId=[b.getId for b in mem_brains],
    ...                             sort_on='made_active_date',
    ...                             sort_order='descending',
    ...                             )
    >>> len(mship_brains)
    3

Zope doesn't want to sort the mship in descending order,
So we do it ourselves here
    >>> from operator import attrgetter
    >>> mship_brains = sorted(mship_brains,
    ...     key=attrgetter('made_active_date'),
    ...     reverse=True)

And now we can simply test that the ids are in the same order
    >>> [a.getId == b.getId for a, b in zip(mem_brains, mship_brains)]
    [True, True, True]

And for good measure, verify that the made active dates are really in
descending order
    >>> active_dates = [b.made_active_date for b in mship_brains]
    >>> active_dates[0] >= active_dates[1] >= active_dates[2]
    True

Clear the memoize from the request::

    >>> utils.clear_all_memos(view)


Sort base on contributions, should get no results::

    >>> results = view.memberships('contributions')
    >>> brains = list(results)
    >>> len(brains)
    0

And check that getting membership roles works
    >>> view.is_admin('m1')
    False
    >>> view.is_admin('m3')
    True

Clear the memoize from the request::
    >>> utils.clear_all_memos(view)

Verify that traversing to the url gives us the expected class::

    >>> view = projects.p1.restrictedTraverse('team')
    >>> view
    <Products.Five.metaclass.SimpleViewClass from ...team-view.pt object at ...>

Call the view to make sure there are no exceptions::

    >>> out = view()

