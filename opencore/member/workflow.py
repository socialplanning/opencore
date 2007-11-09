from zope.component import adapts
from zope.interface import implements

from Products.CMFCore.utils import getToolByName

from opencore.member.interfaces import IOpenMember
from opencore.member.interfaces import IHandleMemberWorkflow

class MemberWorkflowHandler(object):
    adapts(IOpenMember)
    implements(IHandleMemberWorkflow)

    def __init__(self, context):
        self.context = context

    @property
    def _wftool(self):
        return getToolByName(self.context, "portal_workflow")

    @property
    def _wfstate(self):
        return self._wftool.getInfoFor(self.context, "review_state")
        
    def is_unconfirmed(self):
        return self._wfstate == "pending"
