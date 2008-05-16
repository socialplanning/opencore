from zope.interface import Interface, Attribute, implements
from opencore.interfaces import IMemberFolder
from opencore.interfaces.event import IFirstLoginEvent


class IMemberInfo(Interface):
    """
    Information about members and location
    """
    inMemberArea = Attribute("whether or not context is within any member's "
                             "home folder")
    inPersonalArea = Attribute("whether or not context is authenticated "
                               "member's home folder")
    inMemberObject = Attribute("whether or not context is within a member "
                               "object")
    inSelf = Attribute("whether or not context is authenticated member object")
    member = Attribute("member object corresponding to the context's member "
                       "folder or object, if it exists; None if not")


class IMemberHomePage(Interface):
    """ Marker interface for member homepages """



