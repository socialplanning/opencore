from Acquisition import aq_inner
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

class RemoteAuthView(BrowserView):
    """
    Handle remote authentication requests.
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def authenticate(self):
        """
        Extract username and password from request form and return
        simply 'True' or 'False'.
        """
        context = aq_inner(self.context)
        uf = getToolByName(context, 'acl_users')
        form = self.request.form
        result = uf.authenticate(form.get('username'),
                                 form.get('password'),
                                 request)
        if result is None:
            return 'False'
        else:
            return 'True'
