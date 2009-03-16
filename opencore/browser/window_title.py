def window_title(area, context_url, context_title, mode=None):
    """
    mode should be one of: 'view', 'edit', or 'history'.

    Basically this generates a window title that is a breadcrumb list
    of the hierarchy of major "site areas" that contain the current
    view's context object.

    We need to set up an "area" to pass in to the function as the site area
    that contains the current view::
    >>> area = {'Title': 'Best fleem in NYC',
    ...         'absolute_url': '/openplans/projects/fleem-nyc',
    ...         'homepage_url': '/openplans/projects/fleem-nyc/project-home',
    ...         'verbose_title': "Best Fleem in NYC :: OpenCore Site",
    ...        }

    Now we can get some window titles for all sorts of views::
    >>> print window_title(area, "/openplans/projects/fleem-nyc/our-supporters",
    ...                    "People Who Support Great Fleem", 'edit')
    People Who Support Great Fleem (edit) - Best Fleem in NYC :: OpenCore Site

    >>> print window_title(area, "/openplans/projects/fleem-nyc/our-supporters",
    ...                    "People Who Support Great Fleem", 'history')
    People Who Support Great Fleem (history) - Best Fleem in NYC :: OpenCore Site

    The mode 'view' is special and denotes the default view, so there will be
    no parenthetical phrase in the resulting title::
    >>> print window_title(area, "/openplans/projects/fleem-nyc/our-supporters",
    ...                    "People Who Support Great Fleem", 'view')
    People Who Support Great Fleem - Best Fleem in NYC :: OpenCore Site

    If you don't pass in any mode at all, the default 'view' mode is assumed::
    >>> print window_title(area, "/openplans/projects/fleem-nyc/our-supporters",
    ...                    "People Who Support Great Fleem")
    People Who Support Great Fleem - Best Fleem in NYC :: OpenCore Site

    What if the desired view is actually a view on the URL representing the
    area's homepage?
    >>> print window_title(area, area['homepage_url'],
    ...                    "Project Home", 'edit')
    Project Home (edit) - Best Fleem in NYC :: OpenCore Site

    In other words, nothing special -- that is, unless we are looking at the
    DEFAULT view of the area's homepage -- in that case, the entire prefix
    will be dropped from the output::
    >>> print window_title(area, area['homepage_url'],
    ...                    "Project Home")
    Best Fleem in NYC :: OpenCore Site

    And, finally, if we're looking at a view on the area itself, then we
    don't want to redundantly display the area's title twice::
    >>> print window_title(area, area['absolute_url'],
    ...                    "Best fleem in NYC", 'view')
    Best fleem in NYC 

    [Note in the above example that the output actually contains a trailing whitespace character]

    That should hold true even for non-default view modes::
    >>> print window_title(area, area['absolute_url'],
    ...                    "Best fleem in NYC", 'preferences')
    Best fleem in NYC (preferences) 

    [That one too]

    """
    if mode is None:
        mode = 'view'
        
    # if we're rendering the default (view) mode of the area's homepage,
    # we should just display the area title itself
    if mode == 'view' and area['homepage_url'] == context_url:
        return area['verbose_title']

    mode_string = u' '
    if mode != 'view':
        mode_string = u' (%s) '  % mode
    context_string = u'%s%s' % (context_title, mode_string)
        
    if area['absolute_url'] == context_url:
        #If our context is its own area, we shouldn't print its title twice.
        return context_string
    else:
        #If our context is not its own area, we should print the context,
        #and then print the area.
        return u'%s- %s' % (context_string, area['verbose_title'])


def test_suite():
    from pprint import pprint
    from opencore.browser.window_title import window_title
    globs = locals()
    from zope.testing import doctest
    flags = doctest.ELLIPSIS #| doctest.REPORT_ONLY_FIRST_FAILURE
    from opencore.testing import dtfactory as dtf
    octopolite = dtf.ZopeDocFileSuite('window_title.py',
                                      package="opencore.browser",
                                      optionflags=flags,
                                      globs=globs)
    import unittest
    return unittest.TestSuite((octopolite,))


if __name__ == '__main__':
    import unittest
    unittest.TextTestRunner().run(test_suite())
