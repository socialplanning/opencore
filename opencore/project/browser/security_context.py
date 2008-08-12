from opencore.browser.base import BaseView
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class SecurityContextView(BaseView):
    """
    This class returns a 403 unauthorized if the logged-in user cannot view the project.  
    """

    def __call__(self):
        response = self.request.response
        response.setBody("ok")
        return response
