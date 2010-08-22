from opencore.browser.base import BaseView
from Products.CMFCore.utils import getToolByName

OP_PROJECT_HEADER = 'X-OpenPlans-Project'
OP_PERSON_HEADER = 'X-OpenPlans-Person'

class HeaderHijackable(BaseView):
    """
    This is a view class which will switch its
    context based on the values of the X-OpenPlans-*
    header values. 
    """

    # XXX Needs unit tests!

    def _get_context(self):
        if self.request.get_header('HTTP_X_OPENPLANS_APPLICATION') == 'zope':
            return self.original_context
        return self.context_from_headers() or self.original_context
    
    def _set_context(self, ctx):
        # This takes care of doing the right thing in __init__
        self.original_context = ctx
    context = property(_get_context, _set_context)

    def context_from_headers(self):
        return self.person_folder_from_headers() or self.project_from_headers()

    def project_from_headers(self):
        name = self.request.get_header(OP_PROJECT_HEADER)
        if not name:
            return None

        portal = getToolByName(self.original_context,
                               'portal_url').getPortalObject()
        return getattr(portal.projects, name, None)

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
