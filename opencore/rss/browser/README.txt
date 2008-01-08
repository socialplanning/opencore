Verify that for all objects that should provide rss
a view can be obtained

    >>> from zope.component import getMultiAdapter
    >>> request = self.portal.REQUEST

Project
    >>> view = getMultiAdapter((self.portal.projects.p1, request), name='rss')
    >>> html = view()

Projects
    >>> view = getMultiAdapter((self.portal.projects, request), name='rss')
    >>> html = view()

People
    >>> view = getMultiAdapter((self.portal.people, request), name='rss')
    >>> html = view()

Page
    >>> view = getMultiAdapter((self.portal.projects.p1._getOb('project-home'),
    ...                         request),
    ...                         name='rss')
    >>> html = view()
