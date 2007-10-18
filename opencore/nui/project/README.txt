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
    >>> form_vars = dict(id='test1', __initialize_project__=True,
    ...                  workflow_policy='closed_policy',
    ...                  add=True, featurelets = [], set_flets=1)
    >>> view.request.form.update(form_vars)
    >>> view.request.form['title'] = 'testing 1341'
    >>> view.request.form['id'] = 'test1341'
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
    
Preference View
===============

    >>> proj = projects.test1
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

Clear old PSMs

    >>> view.portal_status_message
    [...]


Now set a valid title::
    >>> view.request.form['title'] = 'new full name'
    >>> view.handle_request()
    >>> del view._redirected 
    >>> view.portal_status_message
    [u'The title has been changed.', u'The security policy has been changed.', u'Mailing lists have been removed.']

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

    >>> from opencore.project.browser.projectinfo import get_featurelets
    >>> get_featurelets(proj)
    []

#re-add mailing lists
    >>> view.request.set('flet_recurse_flag', None)
    >>> view.request.form['featurelets'] = ['listen']
    >>> view.handle_request()
    >>> del view._redirected 
    >>> view.portal_status_message
    [u'Mailing lists have been added.']


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

    >>> from opencore.nui.project.team import ProjectTeamView
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
First however, we have to give some members locations
    >>> for mem_id, location in zip(['m1', 'm4', 'm3'], ['ny', 'ny', 'FL']):
    ...     mem = getattr(self.portal.portal_memberdata, mem_id)
    ...     mem.location = location
    ...     mem.reindexObject(idxs=['getLocation'])
    >>> view.sort_by = 'location'
    >>> results = view.memberships
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
    >>> [mem_project.getId() for mem_project in mem_projects]
    ['p2', 'p1', 'p4']
    >>> view.num_projects_for_member(brains[0].getObject())
    3

Clear the memoize from the request::

    >>> utils.clear_all_memos(view)

Let's sort based on the membership date::

    >>> view.sort_by = 'membership_date'
    >>> results = view.memberships
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

