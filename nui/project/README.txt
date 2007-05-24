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
    ...                  workflow_policy='open_policy',
    ...                  add=True)
    >>> view = projects.restrictedTraverse("create")
    >>> view.request.form.update(form_vars)

    >>> out = view.handle_request()
    Traceback (most recent call last):
    ...
    Redirect: http://nohost/plone/projects/test1

    >>> proj = projects.test1
    >>> proj
    <OpenProject at /plone/projects/test1>


# test for featurelet creation

Preference View
===============

    >>> proj.restrictedTraverse('preferences')
    <...SimpleViewClass ...preferences.pt...>

Contents view
=============

    >>> proj.restrictedTraverse('contents')
    <...SimpleViewClass ...contents.pt ...>
