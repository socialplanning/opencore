"""
adapter which determines the scope of wiki link resolution
"""
from Acquisition import aq_parent
from Acquisition import aq_inner

from opencore.interfaces import IOpenPage
from opencore.project.browser.interfaces import IProjectInfo
from wicked.interfaces import IScope
from wicked.interfaces import IAmWickedField
from zope.component import adapts
from zope.interface import implements

class ProjectScope(object):
    """
    Defines a scope of within a contained project, or (if none) the
    parent container.
    """
    implements(IScope)
    adapts(IAmWickedField, IOpenPage)

    def __init__(self, field, context):
        self.field = field
        self.context = context

    def __call__(self):
        projectinfo = IProjectInfo(self.context)
        scope_obj = projectinfo.project
        if scope_obj is None:
            scope_obj = aq_parent(aq_inner(self.context))
        return '/'.join(scope_obj.getPhysicalPath())
