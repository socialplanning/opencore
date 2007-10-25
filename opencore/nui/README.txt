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
    <UIDCatalog at /plone/uid_catalog...>
    
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


Member folder/homepage url
--------

Should get the member folder url for a confirmed member::

    >>> pview.memfolder_url(id_='test_user_1_')
    'http://nohost/plone/people/test_user_1_'

    >>> pview.memfolder_url()
    'http://nohost/plone/people/test_user_1_'

Get homepage url (coming soon)::

    >>> pview.memhome_url()
    'http://nohost/plone/people/test_user_1_/None'




Member info
-----------
See member_info_test.txt.


test nusers and projects_served_count
-------------------------
    >>> pview.nusers()
    5
    >>> pview.projects_served_count()
    4
    >>> members_map = {'new_user':{'fullname':'new user',
    ...                            'password':'testy',
    ...                            'email':'new_user@example.com',
    ...                            'projects':{}}}
    >>> projects_map = {'new_project':{'title':'New Project',
    ...                                'workflow_policy':'closed_policy'}}
    >>> from Products.OpenPlans.Extensions.create_test_content import create_test_content
    >>> self.loginAsPortalOwner() # <-- so we have req'd perms
    >>> create_test_content(self.portal, p_map=projects_map, m_map=members_map)
    'Project new_project added\nMember new_user added'
    >>> self.clearMemoCache()
    >>> pview.nusers()
    6
    >>> pview.projects_served_count()
    5
    >>> self.logout()
    >>> pview.loggedin
    False
    >>> pview.projects_served_count()
    5

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



Search restriction
==================

Add a closed project, and the number of total projects should update (footer)

   The view is the homepage, so let's reuse that. Initially, we should have 4 projects
   >>> self.clearMemoCache()
   >>> view.projects_served_count()
   5

   Let's add a new closed project
   First, let's login as m1
   >>> self.logout()
   >>> self.login('m1')

   >>> self.createClosedProject('new_closed_project')
   <OpenProject at /plone/projects/new_closed_project>

   When querying for number of total projects, we should get
   another result
   >>> self.clearMemoCache()
   >>> view.projects_served_count()
   6

   Now we logout, and we should still get the new project
   >>> self.clearMemoCache()
   >>> self.logout()
   >>> view.projects_served_count()
   6



Title or id for items metadata
------------------------------

Old attachment have no titles thereby do not work in the contents
view::

   >>> self.loginAsPortalOwner()
   >>> from opencore.nui.indexing import metadata_for_portal_content
   >>> from opencore.nui.indexing import metadata_for_brain
   >>> id_ = self.homepage.invokeFactory('FileAttachment', id='someid')
   >>> self.homepage.someid.Title()
   ''

The title is accessed 2 ways, via direct access of the object and
catalog brain::

   >>> catalog = self.portal.portal_catalog
   >>> metadata_for_portal_content(self.homepage.someid, catalog)['Title']
   'someid'

   >>> brain = catalog(getId=id_)[0]
   >>> metadata_for_brain(brain)['Title']
   'someid'
   

Base url on pages set correctly
-------------------------------

The base url must be set properly in the html for relate links to work

   >>> view = self.portal.unrestrictedTraverse('@@view')
   >>> html = view()
   >>> '<base tal:attributes="href string:${context/absolute_url}' in html
   False
   >>> '<base href="http://nohost/plone/" />' in html
   True
