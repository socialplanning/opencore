from Products.TeamSpace.interfaces.team import ITeam
from wicked.interfaces import IAmWicked
from opencore.interfaces.adding import IAddProject
from opencore.interfaces.adding import IAmANewsFolder
from opencore.interfaces.adding import IAmAPeopleFolder
from opencore.interfaces.membership import IOpenMembership
from opencore.interfaces.pending_requests import IPendingRequests
from opencore.interfaces.workflow import IReadWorkflowPolicySupport
from opencore.interfaces.workflow import IWriteWorkflowPolicySupport
from zope.interface import Interface 
from zope.schema import TextLine


class IAddSubProject(Interface):
    """I add sub-projects"""


class IOpenPage(IAmWicked):
    """an openplans wiki page"""


class IMemberFolder(Interface):
    """ Marker interface for member folders """


class IOpenSiteRoot(Interface):
    """ Marker interface for virtual site roots """


class IConsumeNewMembers(Interface):
    """ Marker interface for special projects that consume new members """


class INewsItem(IOpenPage):
    """Marker interface representing a news item"""


class IAmExperimental(Interface):
    """ Marker interface to control new experimental behavior """


class IProject(Interface):
    """Dummy interface for an abstract project class
    """

    def projectMemberIds(admin_only=False):
        """List ids for all the members of this project, optionally limited to
           only admins.
        """

    def projectMembers(admin_only=False):
        """List all the members of this project, optionally limited to
           only admins.
        """

class IEditProject(Interface):
    """Marker interface for OpenProjects edit form
    """

class IOpenTeam(ITeam):
    """
    Interface provided by OpenTeam objects.
    """
    def getProject():
        """Returns the associated project object.

        Tried to make this a python property, but was getting
        attribute errors from the ProjectInfoView.project method.
        """

    def getTeamRolesForMember(mem_id):
        """Returns the team roles for the provided member id.
        """

    def getHighestTeamRoleForMember(mem_id):
        """Returns the team role that provides the highest level of
        permissions for the given member id.  Returns None if the
        member has no corresponding team membership.
        """


class IHomePage(Interface):
    """store a home page attribute on an object"""
    home_page = TextLine(
                    title=u'home page url',
                    description=u"url of object's home page",
                    )

    wiki_notification_list = TextLine(
        title=u'wiki notification list address',
        description=u"email address to send wiki notifications to",
        )
    
