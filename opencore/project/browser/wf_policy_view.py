from Products.Five.browser import BrowserView
from opencore.lib.wf_policy_support import WFPolicyReadAdapter
from opencore.lib.wf_policy_support import ProjectWFPolicyWriteAdapter
from opencore.interfaces import IReadWorkflowPolicySupport
from opencore.interfaces import IWriteWorkflowPolicySupport
from zope.interface import implements

class WorkflowPolicyView(BrowserView, WFPolicyReadAdapter):
    """ A view that has methods for getting information about the
        default workflow policy.  This is implemented as a view rather than an
        adapter because it needs to be accessible via traversal in a template
        for AT edit forms."""

    implements(IReadWorkflowPolicySupport)

class WorkflowPolicyWriterView(BrowserView, ProjectWFPolicyWriteAdapter):
    """ A view that has methods for setting the default workflow policy.  This
        is implemented as a view rather than an adapter because it needs to be 
        accessible via traversal in a template for AT edit forms."""

    implements(IWriteWorkflowPolicySupport)
