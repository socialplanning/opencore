======================
 opencore.nui.project
======================

Add view
========

    >>> projects = self.portal.projects
    >>> projects.restrictedTraverse("create")
    <...SimpleViewClass ...add.pt object ...>

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
    [{'url': 'lists', 'name': 'listen'}]

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
