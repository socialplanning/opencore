from zope.interface import Interface, implements
from zope.app.event.interfaces import IObjectModifiedEvent, IObjectCreatedEvent
from zope.app.event.objectevent import ObjectModifiedEvent, ObjectCreatedEvent
from zope.schema import TextLine

class IAfterProjectAddedEvent(Interface):
    """What happens after a project is added"""


class IAfterSubProjectAddedEvent(IAfterProjectAddedEvent):
    """What happens after a subproject is added"""
    

class IChangedTeamRolesEvent(IObjectModifiedEvent):
    """What happens after a membership object changed roles"""


class IJoinedProjectEvent(IObjectModifiedEvent):
    """When a user becomes an active project member"""


class ILeftProjectEvent(IObjectModifiedEvent):
    """When a user is deactivated from a project"""


class IMemberModifiedEvent(IObjectModifiedEvent):
    """When a user has been modified

       Necessary to add instead of just object modified event because
       the handlers for this can be expensive"""

class IMemberEmailModifiedEvent(IMemberModifiedEvent):
    """
    When a user's email address has been modified

    We have a special event just for this because sometimes
    a subscriber will want to know the old email address from
    before the modification.  It will be stored on the event
    as `.old_email`.
    """
    old_email = TextLine()

class IListenFeatureletCreatedEvent(IObjectCreatedEvent):
    """when a listen featurelet gets installed on a project"""


class IFirstLoginEvent(Interface):
    """ Interface for FirstLoginEvent """


class IMemberRegisteredEvent(Interface):
    """ Interface for member registered event """


class IPortraitModifiedEvent(Interface):
    """ Interface for portrait edit events """


class IMemberDeletedEvent(Interface):
    """ When a member is deleted """

class MemberDeletedEvent(object):
    implements(IMemberDeletedEvent)
    def __init__(self, member):
        self.member = member

class JoinedProjectEvent(ObjectModifiedEvent):
    implements(IJoinedProjectEvent)


class LeftProjectEvent(ObjectModifiedEvent):
    implements(ILeftProjectEvent)


class MemberModifiedEvent(ObjectModifiedEvent):
    implements(IMemberModifiedEvent)

class MemberEmailModifiedEvent(MemberModifiedEvent):
    implements(IMemberEmailModifiedEvent)

    def __init__(self, member, old_email):
        MemberModifiedEvent.__init__(self, member)
        self.context = member
        self.old_email = old_email

class AfterProjectAddedEvent(object):
    implements(IAfterProjectAddedEvent)
    def __init__(self, project, request):
        self.project = project
        self.request = request


class AfterSubProjectAddedEvent(AfterProjectAddedEvent):
    implements(IAfterSubProjectAddedEvent)

    def __init__(self, project, parent, request): 
        AfterProjectAddedEvent.__init__(self, project, request)
        self.parent = parent 


class ChangedTeamRolesEvent(ObjectModifiedEvent):
    implements(IChangedTeamRolesEvent)


class ListenFeatureletCreatedEvent(ObjectCreatedEvent):
    implements(IListenFeatureletCreatedEvent)


class FirstLoginEvent(object):
    implements(IFirstLoginEvent)
    def __init__(self, member, request):
        self.member = member
        self.request = request


class MemberRegisteredEvent(object):
    implements(IMemberRegisteredEvent)
    def __init__(self, member):
        self.member = member


class PortraitModifiedEvent(object):
    implements(IPortraitModifiedEvent)
    def __init__(self, member):
        self.member = member
