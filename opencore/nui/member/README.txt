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
    
    >>> m1_folder.restrictedTraverse("contact")
    <...SimpleViewClass ...contact.pt ...>

This one will need a method alias (projects -> @@projects should work?)::

    >>> m1_folder.restrictedTraverse("@@preferences")
    <...SimpleViewClass from ...preferences.pt...>
