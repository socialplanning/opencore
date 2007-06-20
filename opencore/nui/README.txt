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
    'today'
    
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
efficient(faster) as mixins

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


User/Account methods
====================

    >>> pview.loggedin
    True
    
    >>> pview.loggedinmember
    <OpenMember at /plone/portal_memberdata/test_user_1_>


Home url
--------

Nothing is member isn't confirmed::
    
    >>> pview.home_url_for_id('m1')

Should get the member folder url for a confirmed member::

    >>> pview.home_url_for_id('test_user_1_')
    'http://nohost/plone/people/test_user_1_'

    >>> pview.home_url
    'http://nohost/plone/people/test_user_1_'


Member info
-----------

    >>> pprint(pview.member_info)
    {'affiliations': '',
     'background': '',
     'favorites': '',
     'fullname': '',
     'id': 'test_user_1_',
     'lastlogin': 'January 1, 2000',
     'location': '',
     'membersince': 'today',
     'portrait_url': '++resource++img/default-portrait.jpg',
     'skills': '',
     'statement': '',
     'url': 'http://nohost/plone/people/test_user_1_'}


portal_status_message
=====================

The BaseView class has a property portal_status_message which returns
a list of all portal_status_messages: both those saved in the
plone_utils tool and those passed into the request.

    >>> self.request.form['portal_status_message'] = "I am a banana!"
    >>> view = BaseView(self.homepage, self.request)
    >>> view.portal_status_message
    ['I am a banana!']

include
-------

# @@ needs a test




