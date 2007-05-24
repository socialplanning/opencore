======================
 opencore.nui.project
======================

    >>> projects = self.portal.projects
    >>> request = self.app.REQUEST
    >>> projects.restrictedTraverse("create")
    <...SimpleViewClass ...project-create.pt object ...>

        #<...ProjectAddView object at ...>

    >>> view = projects.restrictedTraverse("create")
    >>> view.request.form.update(dict(title='test1',
    ...                               __initialize_project__=True,
    ...                               full_name='test one',
    ...                               workflow_policy='open_policy'))

    >>> out = view.handleCreate()
    Traceback (most recent call last):
    ...
    Redirect: http://nohost/plone/projects/portal_factory/OpenProject/test1

    >>> projects.test1
    <OpenProject at /plone/projects/test1>
