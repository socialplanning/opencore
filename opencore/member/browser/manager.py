from opencore.browser.viewletmanagers import SortedViewletManager
from zope.interface import implements
from opencore.member.browser import interfaces

class MemberPrefsManager(SortedViewletManager):
    """sorted viewlet manager for project preferences """

    implements(interfaces.IMemberProfilePrefs)
