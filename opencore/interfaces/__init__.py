try:
    from Products.OpenPlans.interfaces import IProject
    from Products.OpenPlans.interfaces import IEditProject
    from Products.OpenPlans.interfaces import IWriteWorkflowPolicySupport
    from Products.OpenPlans.interfaces import IReadWorkflowPolicySupport
except ImportError:
    from zope.interface import Interface
    class IProject(Interface):
        """dummy placeholder"""

from adding import IAddProject
from adding import IAmAPeopleFolder
from adding import IAmANewsFolder

from membership import IOpenMembership

from Products.wicked.interfaces import IAmWicked
from zope.interface import Interface 
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
