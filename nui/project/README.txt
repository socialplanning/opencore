======================
 opencore.nui.project
======================

Add view
========

    >>> projects = self.portal.projects
    >>> projects.restrictedTraverse("create")
    <...SimpleViewClass ...create.pt object ...>

    #<...ProjectAddView object at ...>

    >>> form_vars = dict(title='test1', __initialize_project__=True,
    ...                  full_name='test one',
    ...                  workflow_policy='medium_policy',
    ...                  add=True, featurelets = ['listen'], set_flets=1)
    >>> view = projects.restrictedTraverse("create")
    >>> view.request.form.update(form_vars)

    >>> out = view.handle_request()

    >>> proj = projects.test1
    >>> proj
    <OpenProject at /plone/projects/test1>


# test for featurelet creation

Preference View
===============

    >>> proj.restrictedTraverse('preferences')
    <...SimpleViewClass ...preferences.pt...>

    >>> view = proj.restrictedTraverse('preferences')
    >>> view.project_info['security']
    'medium_policy'

    >>> view.project_info['featurelets']
    [{'url': u'lists', 'name': 'listen', 'title': u'Mailing Lists'}]

    >>> form_vars = dict(title='test one',
    ...                  workflow_policy='closed_policy',
    ...                  update=True,
    ...                  featurelets=[],
    ...                  set_flets=1,
    ...                  __initialize_project__=False)

    >>> view.request.set('flet_recurse_flag', None)
    >>> view.request.form.update(form_vars)
    >>> view.context.REQUEST.form.update(form_vars)

    >>> view.handle_request()
    >>> view = proj.restrictedTraverse('preferences')

    >>> proj.Title()
    'test one'

    >>> IReadWorkflowPolicySupport(proj).getCurrentPolicyId()
    'closed_policy'

    >>> get_featurelets(proj)
    []



#test changing them


Contents view
=============

    >>> proj.restrictedTraverse('contents')
    <...SimpleViewClass ...contents.pt ...>


Team view
=========

Set up the view
    >>> from opencore.nui.project.view import ProjectTeamView
    >>> request = self.portal.REQUEST
    >>> req_annot = IAnnotations(request)
    >>> proj = projects.p1
    >>> view = ProjectTeamView(proj, request)

Utility method to clear memoization on request
    >>> def clear_memo():
    ...     del req_annot['plone.memoize']

Sort by username
    >>> view.sort_by = 'username'
    >>> results = view.memberships
    >>> brains = list(results)
    >>> len(brains)
    3
    >>> [b.getId for b in brains]
    ['m1', 'm3', 'm4']

Clear the memoize from the request
    >>> clear_memo()

Sorting by nothing should sort by username
    >>> view.sort_by = None
    >>> results = view.memberships
    >>> brains = list(results)
    >>> len(brains)
    3
    >>> [b.getId for b in brains]
    ['m1', 'm3', 'm4']

Clear the memoize from the request
    >>> clear_memo()

Now try sorting by location
    >>> view.sort_by = 'location'
    >>> results = view.memberships
    >>> brains = list(results)
    >>> len(brains)
    3
    >>> [b.getId for b in brains]
    ['m4', 'm1', 'm3']

Clear the memoize from the request
    >>> clear_memo()

Let's sort based on the membership date
    >>> view.sort_by = 'membership_date'
    >>> results = view.memberships
    >>> brains = list(results)
    >>> len(brains)
    3
    >>> ids = [b.getId for b in brains]
    >>> ids.sort()
    >>> ids
    ['m1', 'm3', 'm4']

Clear the memoize from the request
    >>> clear_memo()

Sort base on contributions, should get no results
    >>> view.sort_by = 'contributions'
    >>> results = view.memberships
    >>> brains = list(results)
    >>> len(brains)
    0

Clear the memoize from the request
    >>> clear_memo()

Verify that traversing to the url gives us the expected class
    >>> view = projects.p1.restrictedTraverse('team')
    >>> view
    <Products.Five.metaclass.SimpleViewClass from ...team-view.pt object at ...>

Call the view to make sure there are no exceptions
    >>> out = view()
