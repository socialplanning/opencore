from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView

class GetCookie(BrowserView):

    def get_cookie_hash(self):
        if self.request.environ['REQUEST_METHOD'] != "POST":
            return

        mem_folder = self.context
        pm = getToolByName(mem_folder, "portal_membership")
        mem_id = mem_folder.getId()
        member = pm.getMemberById(mem_id)

        pw = self.request.form.get('__ac_password')

        acl = getToolByName(self.context, "acl_users")
        auth = acl.credentials_signed_cookie_auth

        if not member.verifyCredentials(dict(login=mem_id, password=pw)):
            return

        return auth.generateCookie(mem_id)
