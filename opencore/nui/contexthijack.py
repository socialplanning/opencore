"""
"""

from opencore.browser.base import BaseView
from Products.CMFCore.utils import getToolByName

from plone.memoize import view

OP_PROJECT_HEADER = 'X-OpenPlans-Project'
OP_PERSON_HEADER = 'X-OpenPlans-Person'


class HeaderHijackable(BaseView):
    """
    This is a view class which will switch its
    context based on the values of the X-OpenPlans-*
    header values. 
    """
    
    def __init__(self, context, request):
        self.request = request
        self.original_context = context
        
        BaseView.__init__(self, context, request)

    def _get_context(self):
        return self.context_from_headers or self.original_context
    def _set_context(self, ctx):
        self.original_context = ctx
    context = property(_get_context, _set_context)

    @property
    def context_from_headers(self):
        return self.person_folder_from_headers or self.project_from_headers

    @property
    def project_from_headers(self):
        name = self.request.get_header(OP_PROJECT_HEADER)
        if not name:
            return None

        portal = getToolByName(self.original_context,
                               'portal_url').getPortalObject()
        return getattr(portal.projects, name, None)

    @property
    def person_folder_from_headers(self):
        name = self.request.get_header(OP_PERSON_HEADER)

        # don't pass None by accident or it will
        # assume you mean the current user even
        # though you don't. 
        if name:
            mtool = getToolByName(self.original_context,
                                  'portal_membership')
            return mtool.getHomeFolder(name)
        else:
            return None
