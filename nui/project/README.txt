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

    >>> view.project()['security']
    'medium_policy'

    >>> view.project()['featurelets']
    [{'url': 'lists', 'name': 'listen'}]

    >>> form_vars = dict(
    ...                  workflow_policy='closed_policy',
    ...                  add=True, featurelets=[], set_flets=1)
     >>> view.request.form.update(form_vars)

     >>> out = view.handle_request()

     >>> view = proj.restrictedTraverse('preferences')

     >>> view.project()['security']
     'closed_policy'

     >>> view.project()['featurelets']
     []

     >> view.project()['title']

#test changing them


Contents view
=============

    >>> proj.restrictedTraverse('contents')
    <...SimpleViewClass ...contents.pt ...>
