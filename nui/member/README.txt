=====================
 opencore.nui.member
=====================

Test registration of member related views::

    >>> m1_folder = self.portal.people.test_user_1_
    >>> alsoProvides(m1_folder, IMemberFolder)
    >>> m1_folder.restrictedTraverse("profile-edit")
    <...SimpleViewClass ...profile-edit.pt...>

    >>> m1_folder.restrictedTraverse("profile")
    <...SimpleViewClass ...profile.pt object...>
    
    >>> m1_folder.restrictedTraverse("preferences")
    <Products.Five.metaclass.MemberPreferences object at ...>


Exercise the Member Preferences Class
=====================================

    Instantiate the view
    >>> from opencore.nui.member import MemberPreferences
    >>> request = self.app.REQUEST
    >>> request.form = {}
    >>> member = portal.portal_memberdata.m1
    >>> view = MemberPreferences(member, request)
    >>> view
    <opencore.nui.member.view.MemberPreferences object at ...>

    Check projects for user m1
    >>> project_dicts = view.get_projects_for_user()

    Check the projects and active states
    >>> [d['proj_id'] for d in project_dicts]
    ['p2', 'p3', 'p1']
    >>> [d['title'] for d in project_dicts]
    ['Proj2', 'Proj3', 'Proj1']
    >>> [d['listed'] for d in project_dicts]
    [True, True, True]

    XXX invitations are currently stubbed out
    Check invitations for m1
    >>> invitations = view.get_invitations_for_user()
    >>> invitations
    [{'name': 'Big Animals'}, {'name': 'Small Animals'}]

    Check projects for user m2
    reget the view for m2
    >>> member = portal.portal_memberdata.m2
    >>> view = MemberPreferences(member, request)
    >>> project_dicts = view.get_projects_for_user()

    Check the projects and active states
    >>> [d['proj_id'] for d in project_dicts]
    ['p2', 'p3', 'p4']
    >>> [d['title'] for d in project_dicts]
    ['Proj2', 'Proj3', 'Proj4']
    >>> [d['listed'] for d in project_dicts]
    [True, True, True]

    XXX invitations are currently stubbed out
    Check invitations for m2
    >>> invitations = view.get_invitations_for_user()
    >>> invitations
    [{'name': 'Big Animals'}, {'name': 'Small Animals'}]

    Now, let's have a member leave a project::

    But first, if we're not logged in as the member,
    we should get a workflow exception when trying to leave the project
    >>> view.leave_project('p2')
    Traceback (most recent call last):
    ...
    WorkflowException: No workflow provides the "deactivate" action.

    We have to login as m2 to get the modify portal content permission,
    giving us access to the workflow transition
    >>> self.logout()
    >>> self.login('m2')

    Now we should be able to leave the project just fine
    >>> view.leave_project('p2')

    And finally, m2 should no longer have active membership to project p2
    >>> project_dicts = view.get_projects_for_user()
    >>> [d['proj_id'] for d in project_dicts]
    ['p3', 'p4']

    Now we'll try to set the listing as private:

    First though, let's verify that he is currently listed as public
    >>> [d['listed'] for d in project_dicts]
    [True, True]

    Now let's make him private for project 4
    >>> view.change_visibility('p4')

    When we get the projects again, we should not be listed for p4
    >>> project_dicts = view.get_projects_for_user()
    >>> [d['listed'] for d in project_dicts]
    [True, False]

    Now let's set it back to visible
    >>> view.change_visibility('p4')

    Now he should be listed again
    >>> project_dicts = view.get_projects_for_user()
    >>> [d['listed'] for d in project_dicts]
    [True, True]

    Now let's call the view simulating the request:
    XXX Just fake the template for now
    >>> view.template = lambda:None

    Now fake the request
    XXX No interface yet on view to toggle visibility (public/private)
    #>>> request = view.request
    #>>> request.form = dict(action_visibility=True,
    #...                     proj_id='p4')
    #>>> response = view()

    #And we can check the listing status again
    #>>> project_dicts = view.get_projects_for_user()
    #>>> [d['listed'] for d in project_dicts]
    #[True, False]

    Now let's try to leave the project
    >>> request.form = dict(task='p4_leave')
    >>> response = view()

    And now the p4 membership should be missing
    >>> project_dicts = view.get_projects_for_user()
    >>> [d['proj_id'] for d in project_dicts]
    ['p3']
