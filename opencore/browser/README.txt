-*- mode: doctest ;-*-

==============
 opencore.nui
==============

opencore.browser.base
=================

    >>> view = BaseView(self.homepage, self.request)
    >>> view = view.__of__(self.homepage)
    >>> view.portal
    <PloneSite at /plone>
    
    >>> view.dob in ('today', 'yesterday')
    True
    
    >>> view.portal_title()
    u'OpenCore Site'

    >>> pview = BaseView(self.projects.p1, self.request)
    >>> pview = pview.__of__(self.projects.p1)

The properties 'piv' and 'miv' return cached views::

    >>> view.piv
    <...ProjectInfoView object at ...>
    
    >>> view.miv
    <...MemberInfoView object at ...>

They should be properly wrapped(sort of).  The context will be in the
acquisition chain::

    >>> pview.piv.aq_parent
    <opencore.browser.base.BaseView object at ...>

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

These should also be properly wrapped(sort of)::


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

Get homepage url::

    >>> pview.memhome_url()
    'http://nohost/plone/people/test_user_1_/test_user_1_-home'




Member info
-----------
See member_info_test.txt.


test nusers and projects_served_count
-------------------------
    >>> pview.nusers()
    6
    >>> pview.projects_served_count()
    5
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
    7
    >>> pview.projects_served_count()
    6
    >>> self.logout()
    >>> pview.loggedin
    False
    >>> self.clearMemoCache()
    >>> pview.projects_served_count()
    6

portal_status_message
=====================

The BaseView class has a property portal_status_message which returns
a list of all portal_status_messages: both those saved in the
plone_utils tool and those passed into the request.

    >>> self.request.form['portal_status_message'] = "I am a banana!<script>escape this</script>"
    >>> view = BaseView(self.homepage, self.request)
    >>> view.portal_status_message
    ['I am a banana!&lt;script&gt;escape this&lt;/script&gt;']
    
    >>> msg = _(u'psm_test', u'This is a <strong>test</strong> portal status message.  ${this} should be stripped of the script tag.',
    ... mapping={u'this':u'<script>strip this</script>This html'})
    >>> view.add_status_message(msg)
    >>> view.portal_status_message
    [u'This is a <strong>test</strong> portal status message.  This html should be stripped of the script tag.', 'I am a banana!&lt;script&gt;escape this&lt;/script&gt;']


include
-------

# @@ needs a test



Search restriction
==================

Add a closed project, and the number of total projects should update (footer)

   The view is the homepage, so let's reuse that. Initially, we should have 4 projects
   >>> self.clearMemoCache()
   >>> view.projects_served_count()
   6

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
   7

   Now we logout, and we should still get the new project
   >>> self.clearMemoCache()
   >>> self.logout()
   >>> view.projects_served_count()
   7



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

The base url must be set properly in the html for relative links to work

   >>> view = self.portal.unrestrictedTraverse('@@view')

   >>> html = view()
   >>> '<base tal:attributes="href string:${context/absolute_url}' in html
   False
   >>> '<base href="http://nohost/plone/" />' in html
   True


Project-related URLs
--------------------

These should all be looked up via the project_url method.  They
respect the global configuration, let's confirm by patching that:

   >>> view = BaseView(self.homepage, self.request).__of__(self.homepage)

   >>> from opencore.testing import utils
   >>> utils.monkey_proj_noun('project')

   >>> view.project_url()
   'http://nohost/plone/projects'
   >>> view.project_url('proj1')
   'http://nohost/plone/projects/proj1'
   >>> view.project_url(project='proj1')
   'http://nohost/plone/projects/proj1'
   >>> view.project_url(page='somepage')
   'http://nohost/plone/projects/somepage'
   >>> view.project_url(project='proj2', page='another')
   'http://nohost/plone/projects/proj2/another'
 
XXX For now, the project url should not respect the project noun. We still need
generated urls to contain the word ``project`` in them::
   >>> utils.monkey_proj_noun('monkey')
   >>> view.project_url()
   'http://nohost/plone/projects'
   >>> view.project_url('proj1')
   'http://nohost/plone/projects/proj1'
