==================================
 wordpress opencore integration
==================================

** tests don't mean anything right now **

URI convenience api
===================

    >>> from opencore.wordpress import uri as wp_uri

#@@ this should be cleaned up and return none

    >>> tt_uri.get()
    u'http://localhost:5050'

featurelet install
==================

    >>> from opencore.tasktracker.featurelet import TaskTrackerFeaturelet
    >>> ttf = TaskTrackerFeaturelet()

The mock http should be hooked up::

    >>> ttf.http
    <Mock ... httplib2.Http>

We will simulate 'deliverPackage' and 'removePackage', the http calls
to tasktracker::

    >>> project = self.app.plone.projects.p1
    >>> header = {"X-Tasktracker-Initialize":"True"}
    >>> ttf._makeHttpReqAsUser(ttf.init_uri, obj=project, headers=header)
    Called httplib2.Http.request(
        u'http://localhost:5050/project/initialize/',
        headers={'X-Openplans-Project': 'p1', 'Cookie': '__ac=...', 'X-Tasktracker-Initialize': 'True'},
        method='POST')

    >>> ttf._makeHttpReqAsUser(ttf.uninit_uri, obj=project)
    Called httplib2.Http.request(
        u'http://localhost:5050/project/uninitialize/',
        headers={'X-Openplans-Project': 'p1', 'Cookie': '__ac=...'},
        method='POST')
