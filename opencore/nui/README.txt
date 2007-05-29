==============
 opencore.nui
==============

opencore.nui.base
=================

    >>> from opencore.nui.base import BaseView
    >>> view = BaseView(self.homepage, self.request)
    >>> view = view.__of__(self.homepage)
    >>> view.get_portal()
    <PloneSite at /plone>
    
    >>> view.dob_datetime
    DateTime('...')

    >>> view.dob
    'Today'
    
    >>> view.siteURL
    'http://nohost/plone'

    >>> view.sitetitle
    'Portal'


'get_view' retrieves and wraps a view::

    >>> piv0 = view.get_view('project_info')
    >>> piv0.aq_parent
    <OpenPage at /plone/site-home>

Results are cached. Repeated calls to get view should return same
object::

    >>> pview = BaseView(self.projects.p1, self.request)
    >>> pview = pview.__of__(self.projects.p1)
    >>> piv1 = pview.get_view('project_info')
    >>> piv2 = pview.get_view('project_info')
    >>> piv1 == piv2
    True

But not equal views on other contexts::

    >>> piv0 == piv2
    False

The properties 'piv' and 'miv' use 'get_view'::

    >>> view.piv
    <...ProjectInfoView object at ...>
    
    >>> view.miv
    <...MemberInfoView object at ...>

They should be properly wrapped(sort of).  The context will be in the
acquisition chain::

    >>> pview.piv.aq_parent
    <opencore.nui.base.BaseView object at ...>

    >>> pview.piv.aq_parent.aq_parent
    <OpenProject at /plone/projects/p1>

@@ Practical question... does having these as view give use an
advantage over other methods of getting info? they might be more
efficient as mixins

Aliases to commonly used tools are provided and also memoized::

    >>> pview.get_tool('uid_catalog')
    <UIDCatalog at /plone/uid_catalog>
    
    >>> pview.membranetool
    <MembraneTool at /plone/membrane_tool>


    >>> pview.catalog
    <CatalogTool at /plone/portal_catalog>

    >>> pview.membertool
    <MembershipTool at /plone/portal_membership>

    >>> pview.portal_url
    <URLTool at /plone/portal_url>

These should also be properly wrapped(sort of)::

    >>> pview.portal_url.aq_parent
    <opencore.nui.base.BaseView object at ...>


include
-------

# @@ needs a test

loggedin
--------

# @@ needs a test

