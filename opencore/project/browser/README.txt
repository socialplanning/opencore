-*- mode: doctest ;-*- @@ wtf? dwm

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

Now, a valid title and id::
    >>> view.request.form['project_title'] = 'now a valid title!'
    >>> view.request.form['projid'] = 'test1'
    >>> out = view.handle_request()
    opencore.testing.utility.StubCabochonClient: args: ('test1', 'test_user_1_')
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
    opencore.testing.utility.StubCabochonClient: args: ('test1341', 'm2')
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





