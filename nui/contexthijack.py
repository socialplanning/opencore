"""
"""

from opencore.nui.base import BaseView
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
        
        if self.context_from_headers:
            BaseView.__init__(self, self.context_from_headers,
                              request)
        else:
            BaseView.__init__(self, context, request)

    @view.mcproperty
    def context_from_headers(self):
        if self.person_folder_from_headers:
            return self.person_folder_from_headers
        elif self.project_from_headers:
            return self.project_from_headers
        else:
            return None

    @view.mcproperty
    def project_from_headers(self):
        name = self.request.get_header(OP_PROJECT_HEADER)
        if not name:
            return None

        search = getToolByName(self.original_context,
                               'portal_catalog')
        
        objs = search(id=name, portal_type='OpenProject')
        if len(objs) == 1:
            return objs[0].getObject()

        return None

    @view.mcproperty
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
