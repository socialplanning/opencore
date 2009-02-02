==================================
 wordpress opencore integration
==================================

Make sure the WP URI is set up for testing
==========================================

    >>> from opencore.utility.interfaces import IProvideSiteConfig
    >>> from zope.component import getUtility
    >>> getUtility(IProvideSiteConfig)._set('wordpress uri', 'http://nohost:wordpress')

featurelet install
==================

    >>> from opencore.wordpress.featurelet import WordPressFeaturelet
    >>> project = self.app.plone.projects.p1
    >>> wpf = WordPressFeaturelet(project)

The mock http should be hooked up::

    >>> wpf.http
    <HTTPMock ... httplib2.Http>

We will call 'deliverPackage' and 'removePackage', which trigger
the http calls to wordpress::

    >>> wpf.deliverPackage(project)
    Called httplib2.Http.request(
        'http://nohost:wordpress/openplans-create-blog.php',
        ...
    {'menu_items'...}

    >>> wpf.removePackage(project)
    Called httplib2.Http.request(
        'http://nohost:wordpress/openplans-delete-blog.php',
        ...

