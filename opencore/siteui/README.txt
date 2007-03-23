=================
 opencore.siteui
=================
    >>> import pdb; st = pdb.set_trace

tests that have no other home go here

Making sure subprojects listing does not override existing content::

    >>> rproject = self.portal.projects.p1
    >>> rproject.restrictedTraverse("projects")
    <OpenPage at /plone/projects/p1/projects>
    
    >>> alsoProvides(rproject, redirect.IRedirected)

    >>> rproject.restrictedTraverse("projects")
    <...SimpleViewClass from ...subproject_listing.pt object at ...>

    >>> view = rproject.restrictedTraverse("projects")
    >>> view.blocked_content()
    <OpenPage at /plone/projects/p1/projects>

    >>> st(); view()

    >>> import transaction; transaction.commit()
    >>> print http(r'''GET /plone/projects/p1/projects HTTP/1.1''')
