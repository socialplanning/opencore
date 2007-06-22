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
    <...SimpleViewClass ...preferences.pt ...>


Exercise the Member Preferences Class
=====================================

    Instantiate the view
    >>> from opencore.nui.member import MemberPreferences
    >>> request = self.app.REQUEST
    >>> request.form = {}
    >>> member = portal.portal_memberdata.m1
    >>> view = MemberPreferences(member, request)
    >>> view
    <opencore.nui.member.MemberPreferences object at ...>

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
