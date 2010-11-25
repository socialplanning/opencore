from opencore.browser.base import BaseView
from opencore.xinha.i18n import xinha_lang_code

class XinhaConfig(BaseView):

    def xinha_lang_code(self):
        return xinha_lang_code(self.request)

    def in_wordpress(self):
        return self.request["HTTP_X_OPENPLANS_APPLICATION"] == "wordpress"

    def fake_context(self):
        """
        If we're in wordpress, then, as far as xinha's concerned,
        the context is project-home -- this is used for figuring
        out where to hang attachments
        """
        if not self.in_wordpress():
            return self.context
        project = self.request["HTTP_X_OPENPLANS_PROJECT"]
        project = getattr(self.portal.projects, project)
        return project["project-home"]

    def backend_url(self):
        url = self.fake_context().absolute_url() 
        return url + "/internal-link"

    def image_backend_url(self):
        url = self.fake_context().absolute_url()
        return url + "/backend?"
