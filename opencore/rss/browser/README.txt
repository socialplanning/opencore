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

Lists

First need to create a mailing list on a project
    >>> self.login('m3')
    >>> proj = self.portal.projects.p1
    >>> from topp.featurelets.interfaces import IFeatureletSupporter
    >>> fs = IFeatureletSupporter(proj)
    >>> from opencore.listen.featurelet import ListenFeaturelet
    >>> fs.installFeaturelet(ListenFeaturelet(fs))

    >>> lf = self.portal.projects.p1.lists
    >>> view = getMultiAdapter((lf, request), name='rss')
    >>> html = view()

    >>> view = getMultiAdapter((lf._getOb('p1-discussion'),
    ...                         request),
    ...                         name='rss')
    >>> html = view()
