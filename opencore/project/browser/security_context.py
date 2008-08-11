from opencore.browser.base import BaseView
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class SecurityContextView(BaseView):
    """
    This class returns a 403 unauthorized if the logged-in user cannot view the project.  
    """

    def __call__(self):
        mtool = getToolByName(self.context, 'portal_membership')
        result = mtool.checkPermission(View, self.context)
        response = self.request.response
        if result:
            response.setBody("ok")
        else:
            response.setStatus(403)
            response.headers['status'] = 403
        return response
