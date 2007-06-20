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
    >>> view = MemberPreferences(portal, request)
    >>> view
    <opencore.nui.member.MemberPreferences object at ...>

    Check projects for user m1
    >>> self.logout()
    >>> self.login('m1')
    >>> project_dicts = view.get_projects_for_user()

    Check the projects and roles
    >>> [d['title'] for d in project_dicts]
    [u'Proj2', u'Proj3', u'Proj1']
    >>> [d['role'] for d in project_dicts]
    ['ProjectMember', 'ProjectAdmin', 'ProjectMember']

    Check invitations for m1
    >>> invitations = view.get_invitations_for_user()
    >>> invitations
    [{'name': 'Big Animals'}, {'name': 'Small Animals'}]

    XXX invitations are currently stubbed out
    Check projects for user m2
    >>> self.logout()
    >>> self.login('m2')
    >>> project_dicts = view.get_projects_for_user()

    Check the projects and roles
    >>> [d['title'] for d in project_dicts]
    [u'Proj2', u'Proj3', u'Proj4']
    >>> [d['role'] for d in project_dicts]
    ['ProjectMember', 'ProjectMember', 'ProjectAdmin']

    Check invitations for m2
    >>> invitations = view.get_invitations_for_user()
    >>> invitations
    [{'name': 'Big Animals'}, {'name': 'Small Animals'}]
