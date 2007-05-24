#
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
    """I add sub-projects.
    This interface is soley for special-style
    projects that automatically theme users and
    projects created on their site, not
    typical projects that may accept subprojects"""

class IOpenPage(IAmWicked):
    """an openplans wiki page"""
