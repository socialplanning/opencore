======================
 opencore.nui.project
======================

Add view
========

    >>> projects = self.portal.projects
    >>> request = self.app.REQUEST
    >>> projects.restrictedTraverse("create")
    <...SimpleViewClass ...add.pt object ...>

    #<...ProjectAddView object at ...>

    >>> form_vars = dict(title='test1', __initialize_project__=True,
    ...                  full_name='test one',
    ...                  workflow_policy='medium_policy',
    ...                  add=True, featurelets = ['listen'])
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
    ['listen']


Contents view
=============

    >>> proj.restrictedTraverse('contents')
    <...SimpleViewClass ...contents.pt ...>
