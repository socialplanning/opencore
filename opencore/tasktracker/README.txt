==================================
 tasktracker opencore integration
==================================

URI convenience api
===================

    >>> from opencore.utils import get_opencore_property
    >>> get_opencore_property('tasktracker_uri')
    'http://nohost:tasktracker'

featurelet install
==================

    >>> from opencore.tasktracker.featurelet import TaskTrackerFeaturelet
    >>> project = self.app.plone.projects.p1
    >>> ttf = TaskTrackerFeaturelet(project)

The mock http should be hooked up::

    >>> ttf.http
    <HTTPMock ... httplib2.Http>

Calling request(uri) on the mock http will return a (response, content)
tuple like httplib2.Http.request()::
    >>> response, content = ttf.http.request('http://nohost')
    Called ...

The response is set up to return status code 200::
    >>> response.status
    200
    >>> content
    'Mock request succeeded!'

We will simulate 'deliverPackage' and 'removePackage', the http calls
to tasktracker::

    >>> header = {"X-Tasktracker-Initialize":"True"}
    >>> ttf._makeHttpReqAsUser(ttf.init_uri, obj=project, headers=header)
    Called httplib2.Http.request(
        'http://nohost:tasktracker/project/initialize/',
        headers={'X-Openplans-Project': 'p1', 'Cookie': '__ac=...', 'X-Tasktracker-Initialize': 'True'},
        method='POST')
    (<...MockResponse object at ...>, 'Mock request succeeded!')
    >>> ttf._makeHttpReqAsUser(ttf.uninit_uri, obj=project)
    Called httplib2.Http.request(
        'http://nohost:tasktracker/project/uninitialize/',
        headers={'X-Openplans-Project': 'p1', 'Cookie': '__ac=...'},
        method='POST')
    (<...MockResponse object at ...>, 'Mock request succeeded!')

Install a tasktracker featurelet
================================

Make sure we can install a TaskTracker featurelet too::
    >>> self.loginAsPortalOwner()
    >>> form_vars = dict(title='new full name',
    ...                  workflow_policy='closed_policy',
    ...                  update=True,
    ...                  featurelets=['tasks'],
    ...                  set_flets=1,
    ...                  __initialize_project__=False)

    >>> proj = self.portal.projects.p3
    >>> view = proj.restrictedTraverse('preferences')
    >>> view.request.set('flet_recurse_flag', None)
    >>> view.request.form.update(form_vars)
    >>> view.handle_request()
    Called ...

    >>> from opencore.project.utils import get_featurelets
    >>> get_featurelets(proj)
    [{'url': 'tasks', 'name': 'tasks', 'title': u'Tasks'}]
