from opencore.browser.base import BaseView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from opencore.xinha.i18n import xinha_lang_code

class XinhaConfig(BaseView):
    template92 = ZopeTwoPageTemplateFile("xinha-092.pt")
    template96 = ZopeTwoPageTemplateFile("xinha-096.pt")

    def xinha_lang_code(self):
        return xinha_lang_code(self.request, 
                               self.use_new())

    def __call__(self):
        if self.use_new():
            return self.template96()
        return self.template92()

    def use_new(self):
        member = self.loggedinmember
        if member is None:
            return False
        if member.getId() == "greeb":
            return True
        return False
