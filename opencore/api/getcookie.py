from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.remember.interfaces import IReMember


class GetCookie(BrowserView):

    def get_cookie_hash(self):
        if self.request.environ['REQUEST_METHOD'] != "POST":
            self.request.response.setStatus(405)
            return

        mem_folder = self.context
        pm = getToolByName(mem_folder, "portal_membership")
        mem_id = mem_folder.getId()
        member = pm.getMemberById(mem_id)
        if not IReMember.providedBy(member):
            # we're only interested in site members, not root level
            # admins
            self.request.response.setStatus(400)
            return

        pw = self.request.form.get('__ac_password')

        acl = getToolByName(self.context, "acl_users")
        auth = acl.credentials_signed_cookie_auth

        if not member.verifyCredentials(dict(login=mem_id, password=pw)):
            self.request.response.setStatus(400)
            return

        return auth.generateCookie(mem_id)
