==================================
 wordpress opencore integration
==================================

URI convenience api
===================

    >>> from opencore.wordpress import uri as wp_uri

#@@ this should be cleaned up and return none

    >>> wp_uri.get()
    u'http://localhost:8090'

featurelet install
==================

    >>> from opencore.wordpress.featurelet import WordPressFeaturelet
    >>> wpf = WordPressFeaturelet()

The mock http should be hooked up::

    >>> wpf.http
    <HTTPMock ... httplib2.Http>

We will call 'deliverPackage' and 'removePackage', which trigger
the http calls to wordpress::

    >>> project = self.app.plone.projects.p1
    >>> wpf.deliverPackage(project)
    Called httplib2.Http.request(
        u'http://localhost:8090/openplans-create-blog.php',
        ...
    {'menu_items'...}

    >>> wpf.removePackage(project)
    Called httplib2.Http.request(
        u'http://localhost:8090/openplans-delete-blog.php',
        ...
