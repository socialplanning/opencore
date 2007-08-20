======================
 opencore.nui.project
======================

Add view
========

    >>> projects = self.portal.projects
    >>> view = projects.restrictedTraverse("create")
    >>> view
    <Products.Five.metaclass.ProjectAddView object at...>

    >>> form_vars = dict(id='test1', __initialize_project__=True,
    ...                  workflow_policy='medium_policy',
    ...                  add=True, featurelets = ['listen'], set_flets=1)
    >>> view.request.form.update(form_vars)

Try setting some invalid titles::
    >>> view.request.form['title'] = ""
    >>> out = view.handle_request()
    >>> view.errors
    {'title': 'The project name must contain at least 2 characters with at least 1 letter or number.'}
    >>> view.errors = {}

    >>> view.request.form['title'] = "1"
    >>> out = view.handle_request()
    >>> view.errors
    {'title': 'The project name must contain at least 2 characters with at least 1 letter or number.'}
    >>> view.errors = {}

    >>> view.request.form['title'] = "!@#$%"
    >>> out = view.handle_request()
    >>> view.errors
    {'title': 'The project name must contain at least 2 characters with at least 1 letter or number.'}
    >>> view.errors = {}

How about an invalid id?::
    >>> view.request.form['title'] = "valid title"
    >>> view.request.form['id'] = ''
    >>> out = view.handle_request()
    >>> view.errors
    {'id': 'The project url may contain only letters, numbers, hyphens, or underscores and must have at least 1 letter or number.'}
    >>> view.errors = {}

And, another invalid id::
    >>> view.request.form['id'] = 'abcd1-_+'
    >>> out = view.handle_request()
    >>> view.errors
    {'id': 'The project url may contain only letters, numbers, hyphens, or underscores and must have at least 1 letter or number.'}
    >>> view.errors = {}

Now, a valid title and id::
    >>> view.request.form['title'] = 'now a valid title!'
    >>> view.request.form['id'] = 'test1'
    >>> out = view.handle_request()
    >>> view.errors
    {}
    >>> proj = projects.test1
    >>> proj
    <OpenProject at /plone/projects/test1>

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
    >>> self.login('test_user_1_')


Preference View
===============

    >>> proj.restrictedTraverse('preferences')
    <...SimpleViewClass ...preferences.pt...>

    >>> view = proj.restrictedTraverse('preferences')
    >>> view.project_info['security']
    'medium_policy'

    >>> view.project_info['featurelets']
    [{'url': u'lists', 'name': 'listen', 'title': u'Mailing lists'}]

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
    >>> view.request.form['title'] = '?'
    >>> out = view.handle_request()
    >>> view.errors
    {'title': 'The project name must contain at least 2 characters with at least 1 letter or number.'}
    >>> view.errors = {}

Now set a valid title::
    >>> view.request.form['title'] = 'new full name'

    >>> view.handle_request()
    >>> view.errors
    {}
    >>> view = proj.restrictedTraverse('preferences')

    >>> proj.Title()
    'new full name'
    >>> proj.getFull_name()
    'new full name'

    >>> IReadWorkflowPolicySupport(proj).getCurrentPolicyId()
    'closed_policy'

    >>> from opencore.project.browser.projectinfo import get_featurelets
    >>> get_featurelets(proj)
    []

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
    >>> page_id = proj.getDefaultPage()
    >>> page = getattr(proj, page_id)
    >>> page.restrictedTraverse('edit')
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'edit' in this context

    Log back in as the right user
    >>> self.login('test_user_1_')

    Now we can see it again
    >>> proj.restrictedTraverse('preferences')
    <...SimpleViewClass ...preferences.pt...>

Team view
=========

Set up the view::

    >>> from opencore.nui.project.view import ProjectTeamView
    >>> request = self.portal.REQUEST
    >>> proj = projects.p1
    >>> view = ProjectTeamView(proj, request)

Sort by username::

    >>> view.sort_by = 'username'
    >>> results = view.memberships
    >>> brains = list(results)
    >>> len(brains)
    3
    >>> [b.getId for b in brains]
    ['m1', 'm3', 'm4']

Clear the memoize from the request::

    >>> utils.clear_all_memos(view)

Sorting by nothing should sort by username::

    >>> view.sort_by = None
    >>> results = view.memberships
    >>> brains = list(results)
    >>> len(brains)
    3
    >>> [b.getId for b in brains]
    ['m1', 'm3', 'm4']

Clear the memoize from the request::

    >>> utils.clear_all_memos(view)

Now try sorting by location::

    >>> view.sort_by = 'location'
    >>> results = view.memberships
    >>> brains = list(results)
    >>> len(brains)
    3
    >>> [b.getId for b in brains]
    ['m4', 'm1', 'm3']

Test the projects for members work::
    >>> mem_projects = view.projects_for_member(brains[0].getObject())
    >>> [mem_project.getId() for mem_project in mem_projects]
    ['p2', 'p1', 'p4']
    >>> view.num_projects_for_member(brains[0].getObject())
    3

Clear the memoize from the request::

    >>> utils.clear_all_memos(view)

Let's sort based on the membership date::

    >>> view.sort_by = 'membership_date'
    >>> results = view.memberships
    >>> brains = list(results)
    >>> len(brains)
    3
    >>> ids = [b.getId for b in brains]
    >>> ids
    ['m4', 'm1', 'm3']


Clear the memoize from the request::

    >>> utils.clear_all_memos(view)


Sort base on contributions, should get no results::

    >>> view.sort_by = 'contributions'
    >>> results = view.memberships
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

